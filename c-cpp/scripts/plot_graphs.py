#!/usr/bin/env python3
import argparse
from pathlib import Path
import re
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use("Agg")  # non-interactive, safe for servers
import matplotlib.pyplot as plt
import shutil
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.size": 16,  # default text
    "axes.titlesize": 15,  # subplot titles
    "axes.labelsize": 18,  # x and y labels
    "xtick.labelsize": 14,
    "ytick.labelsize": 12,
    "legend.fontsize": 16
})

VALID_RATIOS = {0, 5, 50}
VALID_OPTS = {"base", "foresight", "foresight_SIMD"}

EXCLUDE_IMPL_RE = re.compile(r"^(sequential|sequantial)$", re.IGNORECASE)
FNAME_RE = re.compile(r"^table_(?P<impl>[^_]+)_(?P<opt>.+)_update_(?P<ratio>\d+)p\.csv$")
# Cache file name pattern: table_cache|cahce_{impl}_{opt}_update_{ratio}p_L{level}{metric}_per_tx
CACHE_FNAME_RE = re.compile(
    r"^table_c[ae]che_(?P<impl>[^_]+)_(?P<opt>.+)_update_(?P<ratio>\d+)p_L(?P<level>[13])(?P<metric>miss|ref)_per_tx\.csv$",
    re.IGNORECASE)

COLOR_CYCLE = plt.rcParams["axes.prop_cycle"].by_key()["color"]  # default matplotlib palette
COLOR_MAP = {}  # will be filled once

MARKER_CYCLE = list(Line2D.filled_markers)  # Get the default filled marker cycle
MARKER_MAP = {}  # will be filled once

HATCH_CYCLE = ['', '///', '...', '+++', 'xxx', '---', '\\\\\\', '***']  # for bar graphs
HATCH_MAP = {}  # will be filled once

VERBOSE = False


def vprint(*args, **kwargs):
    if VERBOSE: print(*args, **kwargs)


# Dedicated y-axis labels for derived cache metrics
DERIVED_YLABELS = {
    "L1_miss_rate": "L1 misses per L1 ref",
    "L3_ref_per_L1_ref": "L2 misses per L1 ref",
    "L3_miss_per_L1_ref": "L3 misses per L1 ref",
}


def parse_args():
    ap = argparse.ArgumentParser(description="Generate required graphs from measurement CSVs (with exported legends).")
    ap.add_argument("--tp_indir", required=False, help="Directory containing throughput CSV files")
    ap.add_argument("--indir", required=False, help="Alias for --tp_indir (deprecated)")
    ap.add_argument("--cache_indir", required=True, help="Directory containing cache metric CSV files")
    ap.add_argument("--outdir", default="graphs", help="Directory to write graphs and legends into (default: ./graphs)")
    ap.add_argument("--pattern", default="*.csv", help="Glob (recursively) to find CSVs, default *.csv")
    ap.add_argument("--verbose", action="store_true", help="Enable verbose progress output")
    return ap.parse_args()


def mops(v): return v / 1e7 # dividing by extra 10 since studies run for 10 seconds


def pow2_label(v):
    try:
        iv = int(v)
        if iv > 0 and float(iv) == float(v):
            # Check power of two
            if (iv & (iv - 1)) == 0:
                return f"2^{int(np.log2(iv))}"
    except Exception:
        pass
    return str(v)


def pow2_exp_label(v):
    try:
        iv = int(v)
        if iv > 0 and (iv & (iv - 1)) == 0:
            return str(int(np.log2(iv)))
    except Exception:
        pass
    return str(v)


def pow2_latex(v):
    try:
        iv = int(v)
        if iv > 0 and (iv & (iv - 1)) == 0:
            e = int(np.log2(iv))
            return f"$2^{{{e}}}$"
    except Exception:
        pass
    return str(v)


def series_name(impl, opt): return f"{impl}_{opt}"


def get_color(name):
    # Return consistent color for a given series name.
    if name not in COLOR_MAP:
        # Assign next unused color in cycle
        COLOR_MAP[name] = COLOR_CYCLE[len(COLOR_MAP) % len(COLOR_CYCLE)]
    return COLOR_MAP[name]


def get_marker(name):
    # Return consistent marker for a given series name.
    if name not in MARKER_MAP:
        MARKER_MAP[name] = MARKER_CYCLE[len(MARKER_MAP) % len(MARKER_CYCLE)]
    return MARKER_MAP[name]


def get_hatch(name):
    if name not in HATCH_MAP:
        HATCH_MAP[name] = HATCH_CYCLE[len(HATCH_MAP) % len(HATCH_CYCLE)]
    return HATCH_MAP[name]


def read_all(indir: Path, pattern: str) -> pd.DataFrame:
    files = sorted(indir.rglob(pattern))
    vprint(f"Scanning {indir} for CSVs with pattern '{pattern}' — found {len(files)} files")
    rows = []
    for f in files:
        m = FNAME_RE.match(f.name)
        if not m:
            vprint(f"Skip (name doesn't match): {f.name}")
            continue
        impl, opt, ratio = m.group("impl"), m.group("opt"), int(m.group("ratio"))
        if ratio not in VALID_RATIOS or opt not in VALID_OPTS:  # or EXCLUDE_IMPL_RE.match(impl or ""):
            vprint(f"Skip (filters): impl={impl}, opt={opt}, ratio={ratio} from {f.name}")
            continue
        try:
            df = pd.read_csv(f)
        except Exception as e:
            vprint(f"Skip (read error): {f.name} — {e}")
            continue
        df.columns = [c.strip().lower() for c in df.columns]
        if not {"threads", "init_size", "value"}.issubset(df.columns):
            vprint(f"Skip (missing required columns) in {f.name}: have {list(df.columns)}")
            continue
        df = df[["threads", "init_size", "value"]].copy()
        df["impl"], df["opt"], df["ratio"] = impl, opt, ratio
        rows.append(df)
        vprint(f"Loaded {f.name}: {len(df)} rows (impl={impl}, opt={opt}, ratio={ratio})")
    if rows:
        out = pd.concat(rows, ignore_index=True)
        vprint(f"Total rows loaded: {len(out)}")
        return out
    vprint("No valid CSV rows loaded after filtering.")
    return pd.DataFrame(columns=["threads", "init_size", "value", "impl", "opt", "ratio"])


def read_cache_all(indir: Path, pattern: str) -> pd.DataFrame:
    files = sorted(indir.rglob(pattern))
    vprint(f"Scanning {indir} for CACHE CSVs with pattern '{pattern}' — found {len(files)} files")
    rows = []
    for f in files:
        m = CACHE_FNAME_RE.match(f.name)
        if not m:
            vprint(f"Skip (cache name doesn't match): {f.name}")
            continue
        impl, opt, ratio = m.group("impl"), m.group("opt"), int(m.group("ratio"))
        level, metric = int(m.group("level")), m.group("metric").lower()
        if ratio not in VALID_RATIOS or opt not in VALID_OPTS:
            vprint(f"Skip (cache filters): impl={impl}, opt={opt}, ratio={ratio} from {f.name}")
            continue
        try:
            df = pd.read_csv(f)
        except Exception as e:
            vprint(f"Skip (cache read error): {f.name} — {e}")
            continue
        df.columns = [c.strip().lower() for c in df.columns]
        if not {"threads", "init_size", "value"}.issubset(df.columns):
            vprint(f"Skip (cache missing required columns) in {f.name}: have {list(df.columns)}")
            continue
        df = df[["threads", "init_size", "value"]].copy()
        df["impl"], df["opt"], df["ratio"], df["level"], df["metric"] = impl, opt, ratio, level, metric
        rows.append(df)
        vprint(
            f"Loaded cache {f.name}: {len(df)} rows (impl={impl}, opt={opt}, ratio={ratio}, L{level}, metric={metric})")
    if rows:
        out = pd.concat(rows, ignore_index=True)
        vprint(f"Total cache rows loaded: {len(out)}")
        return out
    vprint("No valid CACHE CSV rows loaded after filtering.")
    return pd.DataFrame(columns=["threads", "init_size", "value", "impl", "opt", "ratio", "level", "metric"])


def build_cache_derived(cache_df: pd.DataFrame) -> list:
    # Build derived ratios from cache metrics:
    # 1) L1 miss / L1 ref (L1 miss rate)
    # 2) L3 ref / L1 ref
    # 3) L3 miss / L1 ref
    if cache_df.empty:
        return []
    key_cols = ["impl", "opt", "ratio", "threads", "init_size"]
    l1ref = cache_df[(cache_df["level"] == 1) & (cache_df["metric"] == "ref")][key_cols + ["value"]].rename(
        columns={"value": "l1ref"})
    l1miss = cache_df[(cache_df["level"] == 1) & (cache_df["metric"] == "miss")][key_cols + ["value"]].rename(
        columns={"value": "l1miss"})
    l3ref = cache_df[(cache_df["level"] == 3) & (cache_df["metric"] == "ref")][key_cols + ["value"]].rename(
        columns={"value": "l3ref"})
    l3miss = cache_df[(cache_df["level"] == 3) & (cache_df["metric"] == "miss")][key_cols + ["value"]].rename(
        columns={"value": "l3miss"})

    base = l1ref
    merged = base
    for other in (l1miss, l3ref, l3miss):
        merged = pd.merge(merged, other, on=key_cols, how="left")

    # Avoid division by zero
    merged = merged.copy()
    merged["l1ref"] = merged["l1ref"].replace({0: np.nan})

    out = []

    def finalize(metric_key: str, value_col: str, label_text: str):
        df = merged[key_cols + [value_col]].dropna().rename(columns={value_col: "value"}).copy()
        if df.empty:
            return
        df["series"] = df.apply(lambda r: series_name(r["impl"], r["opt"]), axis=1)
        out.append((metric_key, label_text, df))

    # L1 miss rate
    merged["l1_miss_rate"] = merged["l1miss"] / merged["l1ref"]
    finalize("L1_miss_rate", "l1_miss_rate", "L1 miss / L1 ref")

    # L3 ref per L1 ref
    merged["l3_ref_per_l1_ref"] = merged["l3ref"] / merged["l1ref"]
    finalize("L3_ref_per_L1_ref", "l3_ref_per_l1_ref", "L3 ref / L1 ref")

    # L3 miss per L1 ref
    merged["l3_miss_per_l1_ref"] = merged["l3miss"] / merged["l1ref"]
    finalize("L3_miss_per_L1_ref", "l3_miss_per_l1_ref", "L3 miss / L1 ref")

    return out


def ensure_outdir(p: Path): p.mkdir(parents=True, exist_ok=True)


# ---------- New: multi-ratio figure builders ----------

def _subplot_tag(i):
    # (a), (b), (c) ...
    return f"({chr(ord('a') + i)})"


def _figure_legend(fig, handles, labels, ncol=None, top_pad=0.02):
    # Put a single legend centered at the top of the figure
    ncol = ncol or max(1, len(labels))
    fig.legend(handles, labels, loc="upper center", ncol=ncol,
               frameon=True, bbox_to_anchor=(0.5, 1.02))
    # Leave some room for the legend
    fig.subplots_adjust(top=1.0 - top_pad)


def _place_title_and_legend(fig, title, handles, labels, ncol=None):
    """
    Put the main title at the very top, the legend just below it,
    and then leave enough top margin so subplot titles won't overlap.
    """
    # 1) Main title on top
    if title:
        fig.suptitle(title, y=1.12, fontsize=16)

    # 2) Legend just below the title (still above subplot titles)
    ncol = ncol or max(1, len(labels))
    fig.legend(handles, labels,
               loc="upper center",
               ncol=ncol,
               frameon=True,
               bbox_to_anchor=(0.5, 1.05))

    # 3) Leave vertical room for both suptitle and legend
    #    so per-subplot titles ("update ratio = X%") won't collide.
    fig.subplots_adjust(top=0.82)


# --- New: allocate a top band for title + legend (no overlap with subplots) ---

def _build_topband_figure(n_subplots, width_per_subplot=6, bottom_height=3,
                          top_ratio=0.30):
    """
    Figure with a dedicated top band (for legend).
    top_ratio controls the height of that band.
    """
    import matplotlib.gridspec as gridspec
    fig_width = width_per_subplot * n_subplots
    fig_height = bottom_height / (1 - top_ratio)
    fig = plt.figure(figsize=(fig_width, fig_height), constrained_layout=False)

    # Margins
    fig.subplots_adjust(left=0.16, right=0.985, bottom=0.10)

    gs = gridspec.GridSpec(
        nrows=2, ncols=n_subplots,
        height_ratios=[top_ratio, 1.0],
        hspace=0.48, wspace=0.30, figure=fig
    )

    ax_top = fig.add_subplot(gs[0, :]);
    ax_top.axis("off")
    ax_row = [fig.add_subplot(gs[1, i]) for i in range(n_subplots)]
    return fig, ax_top, ax_row


def _place_legend_in_topband(ax_top, handles, labels, ncol=None, show=True, one_line=False):
    """
    Place legend in the top band. Options:
      - show=False → skip legend entirely.
      - one_line=True → force all entries into one row (useful for bar plots).
    """
    if not show:
        return

    if one_line:
        ncol = len(labels)  # force one row
    else:
        ncol = ncol or max(1, len(labels))

    leg = ax_top.legend(
        handles, labels,
        loc="upper center",
        ncol=ncol,
        frameon=True,
        bbox_to_anchor=(0.5, 0.90),
        columnspacing=1.0,
        handlelength=2.0,
        labelspacing=0.6,
        borderaxespad=0.0
    )
    for h in leg.legendHandles:
        if hasattr(h, "set_markersize"):
            h.set_markersize(6)


def _place_panel_tags_left(fig, axes, start_char_ord=97, dx=0.045):
    """
    Place '(a),(b),…' left of each axes (figure coords).
    Increase dx to move even farther left.
    """
    fig.canvas.draw()
    for i, ax in enumerate(axes):
        tag = f"({chr(start_char_ord + i)})"
        bbox = ax.get_position()  # figure coords
        x = max(0.0, bbox.x0 - dx)  # farther left than before
        y = bbox.y0 + bbox.height / 2.0
        fig.text(x, y, tag, ha="right", va="center", fontweight="bold")


def _collect_line_handles_labels(series_names):
    # Build dummy handles with the same color/marker mapping we use in plots
    handles, labels = [], []
    for name in series_names:
        h, = plt.plot([], [], marker=get_marker(name), color=get_color(name), linewidth=2, markersize=6,
                      label=str(name))
        handles.append(h);
        labels.append(str(name))
    return handles, labels


def _collect_bar_handles_labels(series_names):
    # Build dummy bar patches with the same color/hatch mapping we use in bar plots
    handles, labels = [], []
    for name in series_names:
        h = plt.Rectangle((0, 0), 1, 1, facecolor=get_color(name), hatch=get_hatch(name),
                          alpha=0.9, edgecolor='black', label=str(name))
        handles.append(h);
        labels.append(str(name))
    return handles, labels


def _panel_prefix(i):
    # 0->(a), 1->(b), ...
    return f"({chr(ord('a') + i)}) "


def make_multi_ratio_line(df, ratios, slice_by, slice_val, x, y, series_list, series_col, outfile,
                          xlabel, ylabel, title=None, show_baseline=False, show_legend=True, one_line=False):
    import matplotlib.ticker as mticker

    n = len(ratios)
    if n == 0:
        return

    # Pick top band size based on legend mode
    if not show_legend:
        top_ratio = 0.01  # very small, almost no band
    elif one_line:
        top_ratio = 0.12  # smaller band for compact one-line legend
    else:
        top_ratio = 0.12  # default, taller band for multi-row legend

    fig, ax_top, axes = _build_topband_figure(n_subplots=n, width_per_subplot=8,
                                              bottom_height=4, top_ratio=top_ratio)

    fig.set_size_inches((n * 6.0), 5.5)

    # Legend content (lines) — use same color/marker maps
    handles, labels = _collect_line_handles_labels(series_list)

    for i, r in enumerate(ratios):
        # handle sequential case differently
        if title.endswith("vs Initial Size (threads=1)"):
            tmp=df[(df["impl"] == "sequential") & (df["ratio"] == r) & (df["threads"] == 1)].copy()
        else:
            tmp=df
        ax = axes[i]
        sub = tmp[(tmp["ratio"] == r) & (tmp[slice_by] == slice_val)].copy()
        if sub.empty:
            ax.text(0.5, 0.5, f"No data (ratio={r}%)", ha="center", va="center", transform=ax.transAxes)
            ax.axis("off")
            continue

        # X preparation
        x_for_plot = x
        if x == "init_size":
            sub = sub.copy()
            sub["_xexp"] = sub["init_size"].apply(lambda v: float(np.log2(int(v))) if v and int(v) > 0 else np.nan)
            x_for_plot = "_xexp"
            sub = sub.sort_values(by=[x_for_plot, series_col])
        else:
            sub = sub.sort_values(by=[x, series_col])

        # Plot series
        present = [s for s in series_list if s in set(sub[series_col].unique())]
        for name in present:
            ssub = sub[sub[series_col] == name]
            if ssub.empty:
                continue
            ax.plot(ssub[x_for_plot], ssub[y], marker=get_marker(name), color=get_color(name), label=str(name))

        # Axes labels
        if x == "init_size":
            xvals = sorted(sub["init_size"].unique().tolist())
            xexp = [int(np.log2(int(v))) for v in xvals]
            ax.set_xticks(xexp, [pow2_latex(v) for v in xvals])
            ax.set_xlabel("Data structure size")
        else:
            ax.set_xlabel(xlabel)
        # --- ylabel only for the first subplot ---
        if i == 0:
            ax.set_ylabel(ylabel)
        else:
            ax.set_ylabel("")  # hide ylabel on other subplots

        # --- title with numbering prefix ---
        ax.set_title(_panel_prefix(i) + f"Update ratio = {r}%", pad=8)

        # Optional baseline for speedup (not used here)
        if show_baseline and y == "speedup":
            ax.axhline(1.0, color="black", linewidth=1.2, alpha=0.6, zorder=0)

        ax.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5, alpha=0.6)

    _place_legend_in_topband(
        ax_top, handles, labels,
        ncol=min(len(labels), max(2, (len(labels) + 1) // 2)),
        show=show_legend,  # normal mode
        one_line=one_line
    )

    vprint(f"Writing combined line figure: {outfile}")
    fig.savefig(outfile, dpi=160, bbox_inches="tight")
    plt.close(fig)


def make_multi_ratio_bar(speed_df, ratios, slice_by, slice_val, x, series_list, series_col, outfile,
                         xlabel, ylabel, title=None, show_legend=True, one_line=False):
    import math
    import matplotlib.ticker as mticker

    n = len(ratios)
    if n == 0:
        return

    # Pick top band size based on legend mode
    if not show_legend:
        top_ratio = 0.01   # very small, almost no band
    elif one_line:
        top_ratio = 0.12   # smaller band for compact one-line legend
    else:
        top_ratio = 0.24   # default, taller band for multi-row legend

    fig, ax_top, axes = _build_topband_figure(n_subplots=n, width_per_subplot=8,
                                            bottom_height=4, top_ratio=top_ratio)

    # Legend content (bars)
    handles, labels = _collect_bar_handles_labels(series_list)

    for i, r in enumerate(ratios):
        ax = axes[i]
        sub = speed_df[(speed_df["ratio"] == r) & (speed_df[slice_by] == slice_val)].copy()
        if sub.empty:
            ax.text(0.5, 0.5, f"No data (ratio={r}%)", ha="center", va="center", transform=ax.transAxes)
            ax.axis("off")
            continue

        # Grouped bars
        xvals = sorted(sub[x].unique().tolist())
        centers = np.arange(len(xvals), dtype=float)
        present = [s for s in series_list if s in set(sub[series_col].unique())]
        nseries, group_width = len(present), 0.8
        bar_w = group_width / max(1, nseries)
        offsets = (np.arange(nseries) - (nseries - 1)/2.0) * (group_width / max(1, nseries))

        all_vals = []
        for j, sv in enumerate(present):
            rows = sub[sub[series_col] == sv]
            yarr = []
            for xv in xvals:
                rsel = rows.loc[rows[x] == xv, "speedup"]
                val = float(rsel.values[0]) if not rsel.empty else np.nan
                yarr.append(val)
                if np.isfinite(val): 
                    all_vals.append(val)

            ax.bar(centers + offsets[j], np.array(yarr) - 1.0,
                   width=bar_w, label=str(sv),
                   color=get_color(sv), hatch=get_hatch(sv),
                   edgecolor='black', alpha=0.9, bottom=1.0)

        # Ticks/labels
        tick_labels = [pow2_latex(v) if x == "init_size" else str(int(v)) for v in xvals]
        ax.set_xticks(centers, tick_labels)
        ax.set_xlabel("Initial data structure size" if x == "init_size" else xlabel)
        # --- ylabel only for the first subplot ---
        if i == 0:
            ax.set_ylabel(ylabel)
        else:
            ax.set_ylabel("")  # hide ylabel on other subplots

        # --- title with numbering prefix ---
        ax.set_title(_panel_prefix(i) + f"Update ratio = {r}%", pad=8)


        # Baseline + smart ylim (0.1 step, one tick above max)
        ax.axhline(1.0, color="black", linewidth=1.2, alpha=0.6, zorder=0)
        if all_vals:
            vmin, vmax = float(np.nanmin(all_vals)), float(np.nanmax(all_vals))
            step = 0.1
            margin_frac = 0.10
            ylow = (1.0 - margin_frac) if vmin >= 1.0 else max(0.0, vmin * (1.0 - margin_frac))
            yhigh = step * math.ceil((vmax + step) / step)
            if yhigh <= ylow: 
                yhigh = ylow + step
            ax.set_ylim(ylow, yhigh)
            ax.yaxis.set_major_locator(mticker.MultipleLocator(step))

        ax.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, alpha=0.6)

    _place_legend_in_topband(
        ax_top, handles, labels,
        ncol=min(len(labels), max(2, (len(labels)+1)//2)),
        show=show_legend,         # switch to False for no legend version
        one_line=one_line     # set True for one-line bar legend
    )


    vprint(f"Writing combined bar figure: {outfile}")
    fig.savefig(outfile, dpi=160, bbox_inches="tight")
    plt.close(fig)

def make_cache_3x3_grid(cache_df: pd.DataFrame,
                        slice_by: str,  # "init_size" or "threads"
                        slice_val: int,
                        series_list: list[str],
                        outfile: Path,
                        show_legend: bool = True,
                        one_line: bool = False):
    """
    3x3 cache grid:
      • Columns = update ratios (0%, 5%, 50%)
      • Rows    = L1 misses, L2 misses, L3 misses
    Adds (a)(b)… numbering to each subplot title and *forces* larger panels by:
      1) Setting figure size in absolute inches (per col/row),
      2) Reserving a fixed-height legend band (in inches), so bottom panels keep their size.
    """
    import matplotlib.gridspec as gridspec

    ratios = sorted(VALID_RATIOS)
    rows = [
        (1, "miss", "L1 misses per tx"),
        (3, "ref", "L2 misses per tx"),
        (3, "miss", "L3 misses per tx"),
    ]
    if cache_df.empty:
        return

    # Determine series that actually appear in this slice
    present_series = set()
    for r in ratios:
        for (lvl, met, _) in rows:
            mask = (
                    (cache_df["ratio"] == r) &
                    (cache_df["level"] == lvl) &
                    (cache_df["metric"] == met) &
                    (cache_df[slice_by] == slice_val)
            )
            if mask.any():
                present_series |= set(cache_df.loc[mask, "series"].unique().tolist())
    present_series = sorted([s for s in series_list if s in present_series], key=str.lower)
    if not present_series:
        return

    # Pre-seed aesthetics for consistency
    for name in present_series:
        _ = get_color(name);
        _ = get_marker(name);
        _ = get_hatch(name)

    ncols, nrows = len(ratios), 3

    # === Absolute sizing knobs (bump these to make panels bigger) ===
    COL_WIDTH_IN = 7  # width of each column (inches) – try 6.5–7.0 if you want more
    ROW_HEIGHT_IN = 4.2  # height of each row (inches) – try 3.9–4.2 if you want more
    LEGEND_HEIGHT_IN = 0.55 if show_legend else 0.08  # fixed legend band (inches)

    # Compute total figure size in inches
    bottom_height_in = nrows * ROW_HEIGHT_IN
    fig_width_in = ncols * COL_WIDTH_IN
    fig_height_in = LEGEND_HEIGHT_IN + bottom_height_in

    # Build the figure and an outer GridSpec with absolute-inch top band
    fig = plt.figure(constrained_layout=False)
    fig.set_size_inches(fig_width_in, fig_height_in)

    # Convert inches to ratios for GridSpec
    top_ratio = LEGEND_HEIGHT_IN / fig_height_in
    bottom_ratio = 1.0 - top_ratio

    outer = gridspec.GridSpec(
        nrows=2, ncols=1,
        height_ratios=[top_ratio, bottom_ratio],
        figure=fig
    )
    ax_top = fig.add_subplot(outer[0, 0]);
    ax_top.axis("off")

    # Inner 3x3 grid for panels
    inner = gridspec.GridSpecFromSubplotSpec(
        nrows=nrows, ncols=ncols, subplot_spec=outer[1, 0],
        # Slightly tighter than before so the extra height goes to the axes
        wspace=0.22, hspace=0.38
    )

    # Margins – keep generous but not wasteful
    fig.subplots_adjust(left=0.095, right=0.990, bottom=0.085, top=0.985)

    # Helper: left-to-right, top-to-bottom panel index for (a)(b)…
    def _panel_idx(row_i: int, col_i: int) -> int:
        return row_i * ncols + col_i  # 0..8

    col_titles = [f"Update ratio = {r}%" for r in ratios]

    for ri, (lvl, met, ylabel) in enumerate(rows):
        for ci, r in enumerate(ratios):
            ax = fig.add_subplot(inner[ri, ci])
            sub = cache_df[
                (cache_df["ratio"] == r) &
                (cache_df["level"] == lvl) &
                (cache_df["metric"] == met) &
                (cache_df[slice_by] == slice_val)
                ].copy()
            
            # handle sequential case differently
            if slice_val==1:
                sub=sub[(sub["impl"] == "sequential")].copy()

            if sub.empty:
                ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
                ax.axis("off")
                ax.set_title(_panel_prefix(_panel_idx(ri, ci)) + col_titles[ci], pad=8)
                continue

            # --- Uniform categorical x-axis ---
            if slice_by == "init_size":
                x_key = "threads"
                xvals = sorted(sub[x_key].unique().tolist())
                xticklabels = [str(int(v)) for v in xvals]
                xlabel_text = "Threads"
            else:
                x_key = "init_size"
                xvals = sorted(sub[x_key].unique().tolist())
                xticklabels = [pow2_latex(v) for v in xvals]
                xlabel_text = "Data structure size"

            xpos = np.arange(len(xvals), dtype=float)
            ax.set_xticks(xpos)
            ax.set_xticklabels(xticklabels)
            ax.set_xlabel(xlabel_text if ri == (nrows - 1) else "")

            # Plot each series aligned to categorical positions
            avail = set(sub["series"].unique().tolist())
            to_plot = [s for s in present_series if s in avail]
            for name in to_plot:
                ssub = sub[sub["series"] == name]
                if ssub.empty:
                    continue
                lookup = ssub.set_index(x_key)["value"].to_dict()
                yvals = [float(lookup.get(x, np.nan)) for x in xvals]
                ax.plot(xpos, yvals, marker=get_marker(name), color=get_color(name),
                        label=str(name), linewidth=2)

            # Row y-label on first column only
            ax.set_ylabel(ylabel if ci == 0 else "")

            # Numbered title on EVERY subplot
            ax.set_title(_panel_prefix(_panel_idx(ri, ci)) + col_titles[ci], pad=8)

            ax.margins(x=0.05)
            ax.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5, alpha=0.6)
            ax.tick_params(axis='x', labelrotation=0)

    # Legend in the top band (optional)
    if show_legend:
        handles, labels = _collect_line_handles_labels(present_series)
        _place_legend_in_topband(
            ax_top, handles, labels,
            ncol=min(len(labels), max(2, (len(labels) + 1) // 2)),
            show=True,
            one_line=one_line
        )

    vprint(f"Writing cache 3x3 grid: {outfile}")
    fig.savefig(outfile, dpi=160, bbox_inches="tight")
    plt.close(fig)

def make_derived_cache_3x3_grid(
    cache_df:    pd.DataFrame,
    slice_by:    str,   # 'init_size' or 'threads'
    slice_val:   int,
    series_list: list[str],
    outfile:    Path,
    show_legend: bool = True,
    one_line:    bool = False,
):
    """
    3x3 grid of DERIVED cache-ratio metrics.
    Columns : update ratios (0, 5, 50)
    Rows    : L1 miss / L1 ref  |  L3 ref / L1 ref  |  L3 miss / L1 ref
    """
    import matplotlib.gridspec as gridspec

    if cache_df.empty:
        return

    ratios    = sorted(VALID_RATIOS)
    # row definition: (metric_key, y-axis label)
    row_defs = [
        ('L1_miss_rate',       'L1 miss / L1 ref'),
        ('L3_ref_per_L1_ref',  'L2 miss / L1 ref'),
        ('L3_miss_per_L1_ref', 'L3 miss / L1 ref'),
    ]
    ncols, nrows = len(ratios), len(row_defs)

    # ------------------------------------------------------------------ #
    # Build derived frames for every ratio, keyed by (ratio, metric_key)  #
    # ------------------------------------------------------------------ #
    derived_lookup = {}   # (ratio, metric_key) -> DataFrame with cols [threads, init_size, ratio, series, value]
    for r in ratios:
        subr = cache_df[cache_df['ratio'] == r].copy()
        if subr.empty:
            continue
        for key, labeltext, ddf in build_cache_derived(subr):
            derived_lookup[(r, key)] = ddf   # ddf has: keycols + 'value' + 'series'

    # Determine which series actually appear across all panels
    present_series = set()
    for (r, key), ddf in derived_lookup.items():
        mask = ddf[slice_by] == slice_val
        if mask.any():
            present_series.update(ddf.loc[mask, 'series'].unique().tolist())
    present_series = sorted(
        [s for s in series_list if s in present_series], key=str.lower
    )
    if not present_series:
        return

    # Pre-seed color/marker for consistency
    for name in present_series:
        get_color(name); get_marker(name); get_hatch(name)

    # ------------------------------------------------------------------ #
    # Figure layout  (identical knobs to make_cache_3x3_grid)             #
    # ------------------------------------------------------------------ #
    COL_WIDTH_IN    = 7
    ROW_HEIGHT_IN   = 4.2
    LEGEND_HEIGHT_IN = 0.55 if show_legend else 0.08

    bottom_height_in = nrows * ROW_HEIGHT_IN
    figwidth_in      = ncols * COL_WIDTH_IN
    figheight_in     = LEGEND_HEIGHT_IN + bottom_height_in

    fig = plt.figure(constrained_layout=False)
    fig.set_size_inches(figwidth_in, figheight_in)

    topratio   = LEGEND_HEIGHT_IN / figheight_in
    bottomratio = 1.0 - topratio
    outer = gridspec.GridSpec(
        nrows=2, ncols=1,
        height_ratios=[topratio, bottomratio],
        figure=fig,
    )
    axtop = fig.add_subplot(outer[0, 0])
    axtop.axis('off')

    inner = gridspec.GridSpecFromSubplotSpec(
        nrows=nrows, ncols=ncols,
        subplot_spec=outer[1, 0],
        wspace=0.22, hspace=0.38,
    )
    fig.subplots_adjust(left=0.095, right=0.990, bottom=0.085, top=0.985)

    def panel_idx(rowi: int, coli: int) -> int:
        return rowi * ncols + coli

    col_titles = [f'Update ratio {r}' for r in ratios]

    # ------------------------------------------------------------------ #
    # Draw panels                                                          #
    # ------------------------------------------------------------------ #
    for ri, (metric_key, ylabel) in enumerate(row_defs):
        for ci, r in enumerate(ratios):
            ax  = fig.add_subplot(inner[ri, ci])
            ddf = derived_lookup.get((r, metric_key), pd.DataFrame())

            if ddf.empty:
                ax.text(0.5, 0.5, f'No data\nratio={r}',
                        ha='center', va='center', transform=ax.transAxes)
                ax.axis('off')
                ax.set_title(_panel_prefix(panel_idx(ri, ci)) + col_titles[ci], pad=8)
                continue

            sub = ddf[ddf[slice_by] == slice_val].copy()

            if sub.empty:
                ax.text(0.5, 0.5, 'No data',
                        ha='center', va='center', transform=ax.transAxes)
                ax.axis('off')
                ax.set_title(_panel_prefix(panel_idx(ri, ci)) + col_titles[ci], pad=8)
                continue

            # X-axis setup
            if slice_by == 'init_size':
                xkey       = 'threads'
                xvals      = sorted(sub[xkey].unique().tolist())
                xticklabels = [str(int(v)) for v in xvals]
                xlabel_text = 'Threads'
            else:
                xkey       = 'init_size'
                xvals      = sorted(sub[xkey].unique().tolist())
                xticklabels = [pow2_latex(v) for v in xvals]
                xlabel_text = 'Data structure size'

            xpos = np.arange(len(xvals), dtype=float)
            ax.set_xticks(xpos)
            ax.set_xticklabels(xticklabels)
            if ri == nrows - 1:
                ax.set_xlabel(xlabel_text)
            else:
                ax.set_xlabel('')

            # Plot each series
            avail  = set(sub['series'].unique().tolist())
            toplot = [s for s in present_series if s in avail]
            for name in toplot:
                ssub   = sub[sub['series'] == name]
                if ssub.empty:
                    continue
                lookup = ssub.set_index(xkey)['value'].to_dict()
                yvals  = [float(lookup.get(x, np.nan)) for x in xvals]
                ax.plot(xpos, yvals,
                        marker=get_marker(name), color=get_color(name),
                        label=str(name), linewidth=2)

            ax.set_ylabel(ylabel if ci == 0 else '')
            ax.set_title(_panel_prefix(panel_idx(ri, ci)) + col_titles[ci], pad=8)
            ax.margins(x=0.05)
            ax.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5, alpha=0.6)
            ax.tick_params(axis='x', labelrotation=0)

    # Legend
    if show_legend:
        handles, labels = _collect_line_handles_labels(present_series)
        _place_legend_in_topband(
            axtop, handles, labels,
            ncol=min(len(labels), max(2, (len(labels) + 1) // 2)),
            show=True, one_line=one_line,
        )

    vprint(f'Writing derived cache 3x3 grid → {outfile}')
    fig.savefig(outfile, dpi=160, bbox_inches='tight')
    plt.close(fig)


# ---------- Plot helpers ----------

def line_plot(df, x, y, all_series, series_col, title, outpath, xlabel_override=None, ylabel_override=None,
              show_title=True):
    plt.figure()  # width=6 inches, height=2.5 inches
    # Prepare x-axis, with special handling for init_size to ensure uniform spacing using log2
    x_for_plot = x
    if x == "init_size":
        df = df.copy()
        df["_xexp"] = df[x].apply(lambda v: float(np.log2(int(v))) if v and int(v) > 0 else np.nan)
        x_for_plot = "_xexp"
        df = df.sort_values(by=[x_for_plot, series_col])
    elif x in df.columns and pd.api.types.is_numeric_dtype(df[x]):
        df = df.sort_values(by=[x, series_col])
    present = [s for s in all_series if s in set(df[series_col].unique())]
    for name in present:
        sub = df[df[series_col] == name]
        if not sub.empty:
            plt.plot(sub[x_for_plot], sub[y], marker=get_marker(name), label=str(name), color=get_color(name))
    if x == "init_size":
        xvals = sorted(df[x].unique().tolist())
        xexp = [int(np.log2(int(v))) for v in xvals]
        plt.xticks(xexp, [pow2_latex(v) for v in xvals])
        plt.xlabel("Data structure size")
    else:
        plt.xlabel(x)
    if xlabel_override is not None: plt.xlabel(xlabel_override)
    plt.ylabel(y)
    if ylabel_override is not None: plt.ylabel(ylabel_override)
    # Baseline line for speedup plots (slightly emphasized)
    if y == "speedup":
        plt.axhline(1.0, color="black", linewidth=1.2, alpha=0.6, zorder=0)
    if show_title:
        plt.title(title)
    plt.grid(True, which='both', axis='both', linestyle='--', linewidth=0.5, alpha=0.6)
    plt.tight_layout();
    vprint(f"Writing line plot: {outpath}");
    plt.savefig(outpath, dpi=160);
    plt.close()


def grouped_bar_plot(df, x, y, all_series, series_col, title, outpath,
                     xlabel_override=None, ylabel_override=None, show_title=True):
    plt.figure(figsize=(6, 3))
    xvals = sorted([int(v) if isinstance(v, (np.integer,)) else v for v in df[x].unique().tolist()])
    if len(xvals) == 0:
        plt.close();
        return

    centers = np.arange(len(xvals), dtype=float)
    present = [s for s in all_series if s in set(df[series_col].unique())]
    if not present:
        plt.close();
        return

    nseries, group_width = len(present), 0.8
    bar_w = group_width / max(1, nseries)
    offsets = (np.arange(nseries) - (nseries - 1) / 2.0) * (group_width / max(1, nseries))

    # Collect all bar values to compute smart y-limits
    all_vals = []

    for i, sv in enumerate(present):
        sub, yarr = df[df[series_col] == sv], []
        for xv in xvals:
            row = sub[sub[x] == xv]
            val = float(row.iloc[0][y]) if not row.empty else np.nan
            yarr.append(val)
            if np.isfinite(val):
                all_vals.append(val)

        plt.bar(centers + offsets[i], np.array(yarr) - 1.0, width=bar_w, label=str(sv),
                color=get_color(sv), hatch=get_hatch(sv),
                edgecolor='black', alpha=0.9, bottom=1.0)

    tick_labels = [pow2_latex(v) if x == "init_size" else str(v) for v in xvals]
    plt.xticks(centers, tick_labels)
    plt.xlabel("Data structure size" if x == "init_size" else x)
    if xlabel_override is not None: plt.xlabel(xlabel_override)
    plt.ylabel(y)
    if ylabel_override is not None: plt.ylabel(ylabel_override)

    import matplotlib.ticker as mticker
    import math

    if y == "speedup":
        plt.axhline(1.0, color="black", linewidth=1.2, alpha=0.6, zorder=0)

        if all_vals:
            vmin, vmax = float(np.nanmin(all_vals)), float(np.nanmax(all_vals))
            margin_frac = 0.10  # margin near data

            # ----- bottom limit as before -----
            if vmin >= 1.0:
                ylow = 1.0 - margin_frac
            else:
                ylow = max(0.0, vmin * (1.0 - margin_frac))

            # ----- top limit: next tick above max -----
            step = 0.1
            yhigh = step * math.ceil((vmax + step) / step)  # one tick above vmax

            # safeguard
            if yhigh <= ylow:
                yhigh = ylow + step

            plt.ylim(ylow, yhigh)

            # force ticks every 0.1
            plt.gca().yaxis.set_major_locator(mticker.MultipleLocator(step))

    if show_title:
        plt.title(title)

    plt.grid(True, which='both', axis='y', linestyle='--', linewidth=0.5, alpha=0.6)
    plt.tight_layout()
    vprint(f"Writing grouped bar plot: {outpath}")
    plt.savefig(outpath, dpi=160)
    plt.close()


def build_speedup(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["opt"] == "base"][["impl", "threads", "init_size", "ratio", "value"]].rename(
        columns={"value": "base_val"})
    non = df[df["opt"] != "base"][["impl", "opt", "threads", "init_size", "ratio", "value"]]
    merged = pd.merge(non, base, on=["impl", "threads", "init_size", "ratio"], how="inner")
    merged["speedup"] = merged["value"] / merged["base_val"]
    merged["series"] = merged.apply(lambda r: series_name(r["impl"], r["opt"]), axis=1)
    return merged


# ---------- Legend helpers (now split into two outputs) ----------

def export_line_legend(series_names, outpath, ncol=None):
    """Legend for line plots only (no bar patches)."""
    fig, ax = plt.subplots()
    handles, labels = [], []
    for name in series_names:
        line_handle, = ax.plot([], [], marker=get_marker(name), label=str(name),
                               color=get_color(name), markersize=8, linewidth=2)
        handles.append(line_handle)
        labels.append(str(name))
    num_cols = ncol if (ncol is not None) else max(1, len(labels))
    ax.legend(handles=handles, labels=labels, loc='center', frameon=True, ncol=num_cols)
    ax.axis('off')
    fig.tight_layout()
    vprint(f"Writing line legend: {outpath}")
    fig.savefig(outpath, dpi=160, bbox_inches='tight')
    plt.close(fig)


def export_bar_legend(series_names, outpath, ncol=None):
    """Legend for bar plots only (uses same COLOR_MAP/HATCH_MAP)."""
    fig, ax = plt.subplots()
    handles, labels = [], []
    for name in series_names:
        bar_handle = plt.Rectangle((0, 0), 1, 1,
                                   facecolor=get_color(name),
                                   hatch=get_hatch(name),
                                   alpha=0.9,
                                   edgecolor='black')
        handles.append(bar_handle)
        labels.append(str(name))
    num_cols = ncol if (ncol is not None) else max(1, len(labels))
    ax.legend(handles=handles, labels=labels, loc='center', frameon=True, ncol=num_cols)
    ax.axis('off')
    fig.tight_layout()
    vprint(f"Writing bar legend: {outpath}")
    fig.savefig(outpath, dpi=160, bbox_inches='tight')
    plt.close(fig)


# ---------- Main ----------

def main():
    args = parse_args()
    tp_dir_arg = args.tp_indir or args.indir
    if not tp_dir_arg:
        print("--tp_indir (or --indir) is required for throughput CSVs");
        return
    indir, cache_indir, outdir = Path(tp_dir_arg).resolve(), Path(args.cache_indir).resolve(), Path(
        args.outdir).resolve()
    global VERBOSE;
    VERBOSE = bool(args.verbose)
    if outdir.exists():
        vprint(f"Clearing existing output directory: {outdir}")
        shutil.rmtree(outdir, ignore_errors=True)
    ensure_outdir(outdir)
    vprint(f"Output directory ready: {outdir}")

    if (indir.name.startswith("seq_")): # adjust to sequential case
        THREAD_COUNTS_FOR_SLICE = [1]
        INIT_SIZES_FOR_SLICE = []
    else:
        THREAD_COUNTS_FOR_SLICE = [128]
        INIT_SIZES_FOR_SLICE = [33554432]

    # Load data
    df = read_all(indir, args.pattern)
    if df.empty: print("No matching throughput CSVs found."); return
    df["mops"], df["series"] = df["value"].apply(mops), df.apply(lambda r: series_name(r["impl"], r["opt"]), axis=1)

    cache_df = read_cache_all(cache_indir, args.pattern)
    if not cache_df.empty:
        cache_df["series"] = cache_df.apply(lambda r: series_name(r["impl"], r["opt"]), axis=1)

    # Determine families of series per ratio (unchanged)
    family_series = {}
    for r in sorted(VALID_RATIOS):
        sub = df[df["ratio"] == r]
        raw_series = sorted(sub["series"].unique().tolist(), key=str.lower)
        sp_series = sorted(build_speedup(sub)["series"].unique().tolist(), key=str.lower)
        family_series[("raw_init", r)] = raw_series
        family_series[("raw_thr", r)] = raw_series
        family_series[("sp_init", r)] = sp_series
        family_series[("sp_thr", r)] = sp_series
        vprint(
            f"Series for ratio {r}%: raw_init={len(raw_series)}, sp_init={len(sp_series)}, raw_thr={len(raw_series)}, sp_thr={len(sp_series)}")

    # --------- Build global series lists for legends ----------
    # Line legend: include *all* series that may appear in any line plot (throughput, speedup-line, cache)
    line_series_all = set(df["series"].unique().tolist())
    # Speedup line plots also use non-base series (already included via df["series"]), and cache_df may add more:
    if not cache_df.empty:
        line_series_all |= set(cache_df["series"].unique().tolist())
    line_series_all = sorted(line_series_all, key=str.lower)

    # Bar legend: only the series that appear in bar plots (non-base in speedup)
    sp_series_all = sorted(df[df["opt"] != "base"]["series"].unique().tolist(), key=str.lower)

    # Pre-seed mappings so colors/hatches/markers are consistent across both legends and plots
    for name in sorted(set(line_series_all) | set(sp_series_all), key=str.lower):
        _ = get_color(name);
        _ = get_marker(name);
        _ = get_hatch(name)

    # Export two separate legends
    if line_series_all:
        ncol_lines = (len(line_series_all) + 1) // 2  # two rows when many items
        export_line_legend(line_series_all, outdir / "legend_lines.png", ncol=ncol_lines)
    if sp_series_all:
        ncol_bars = (len(sp_series_all) + 1) // 2
        export_bar_legend(sp_series_all, outdir / "legend_bars.png", ncol=ncol_bars)

    # ---------- Plots (unchanged logic) ----------
    for r in sorted(VALID_RATIOS):
        all_series_raw, all_series_sp = family_series.get(("raw_init", r), []), family_series.get(("sp_init", r), [])
        ratio_dir = outdir / f"update_ratio_{r}"
        ensure_outdir(ratio_dir)
        vprint(f"Ratio directory ready: {ratio_dir}")
        for t in THREAD_COUNTS_FOR_SLICE:
            if t != 1:
                slice_df = df[(df["ratio"] == r) & (df["threads"] == t)].copy()
            else:
                slice_df = df[(df["impl"] == "sequential") & (df["ratio"] == r) & (df["threads"] == t)].copy()
            if slice_df.empty: continue
            raw = slice_df[["init_size", "mops", "series"]].drop_duplicates()
            if not raw.empty and all_series_raw:
                line_plot(raw, "init_size", "mops", all_series_raw, "series",
                          f"Throughput (Mops) vs init_size | ratio={r}% | threads={t}",
                          ratio_dir / f"threads_{t}_tp.png",
                          xlabel_override="Data structure size", ylabel_override="Throughput (Mops)",
                          show_title=False)
            sp = build_speedup(slice_df)
            if not sp.empty and all_series_sp:
                speed_df = sp[["init_size", "speedup", "series"]].drop_duplicates()
                line_plot(speed_df, "init_size", "speedup", all_series_sp, "series",
                          f"Speedup vs base by init_size | ratio={r}% | threads={t}",
                          ratio_dir / f"threads_{t}_speedup_line.png",
                          xlabel_override="Data structure size", ylabel_override="Speedup", show_title=False)
                grouped_bar_plot(speed_df, "init_size", "speedup", all_series_sp, "series",
                                 f"Speedup vs base by init_size | ratio={r}% | threads={t}",
                                 ratio_dir / f"threads_{t}_speedup_bar.png",
                                 xlabel_override="Data structure size", ylabel_override="Speedup",
                                 show_title=False)

    for r in sorted(VALID_RATIOS):
        all_series_raw, all_series_sp = family_series.get(("raw_thr", r), []), family_series.get(("sp_thr", r), [])
        ratio_dir = outdir / f"update_ratio_{r}"
        ensure_outdir(ratio_dir)
        vprint(f"Ratio directory ready: {ratio_dir}")
        for s in INIT_SIZES_FOR_SLICE:
            slice_df = df[(df["ratio"] == r) & (df["init_size"] == s)].copy()
            if slice_df.empty: continue
            raw = slice_df[["threads", "mops", "series"]].drop_duplicates()
            if not raw.empty and all_series_raw:
                line_plot(raw, "threads", "mops", all_series_raw, "series",
                          f"Throughput (Mops) vs threads | ratio={r}% | init_size={pow2_latex(s)}",
                          ratio_dir / f"init_size_{s}_tp.png",
                          xlabel_override="Threads", ylabel_override="Throughput (Mops)", show_title=False)
            sp = build_speedup(slice_df)
            if not sp.empty and all_series_sp:
                speed_df = sp[["threads", "speedup", "series"]].drop_duplicates()
                line_plot(speed_df, "threads", "speedup", all_series_sp, "series",
                          f"Speedup vs base by threads | ratio={r}% | init_size={pow2_latex(s)}",
                          ratio_dir / f"init_size_{s}_speedup_line.png",
                          xlabel_override="Threads", ylabel_override="Speedup", show_title=False)
                grouped_bar_plot(speed_df, "threads", "speedup", all_series_sp, "series",
                                 f"Speedup vs base by threads | ratio={r}% | init_size={pow2_latex(s)}",
                                 ratio_dir / f"init_size_{s}_speedup_bar.png",
                                 xlabel_override="Threads", ylabel_override="Speedup", show_title=False)

    # Cache metric plots (replicate tp-style plots) if cache data is provided
    if not cache_df.empty:
        for r in sorted(VALID_RATIOS):
            ratio_dir = outdir / f"update_ratio_{r}"
            ensure_outdir(ratio_dir)
            vprint(f"Ratio directory ready for cache: {ratio_dir}")
            sub_r = cache_df[cache_df["ratio"] == r]
            if sub_r.empty: continue
            # Use same series ordering as throughput for consistent colors
            cache_series = sorted(sub_r["series"].unique().tolist(), key=str.lower)
            # By (level, metric)
            for (level, metric) in sorted(
                    sub_r[["level", "metric"]].drop_duplicates().itertuples(index=False, name=None)):
                # By init_size for fixed threads
                for t in THREAD_COUNTS_FOR_SLICE:
                    slice_df = sub_r[
                        (sub_r["threads"] == t) & (sub_r["level"] == level) & (sub_r["metric"] == metric)].copy()
                    if slice_df.empty: continue
                    raw = slice_df[["init_size", "value", "series"]].drop_duplicates().rename(columns={"value": "val"})
                    line_plot(raw.rename(columns={"val": "value"}), "init_size", "value", cache_series, "series",
                              f"Cache L{level} {metric} per tx vs init_size | ratio={r}% | threads={t}",
                              ratio_dir / f"threads_{t}_cache_L{level}_{metric}.png",
                              xlabel_override="Data structure size",
                              ylabel_override=f"L{level} {metric} per tx", show_title=False)
                # By threads for fixed init_size
                for s in INIT_SIZES_FOR_SLICE:
                    slice_df = sub_r[
                        (sub_r["init_size"] == s) & (sub_r["level"] == level) & (sub_r["metric"] == metric)].copy()
                    if slice_df.empty: continue
                    raw = slice_df[["threads", "value", "series"]].drop_duplicates().rename(columns={"value": "val"})
                    line_plot(raw.rename(columns={"val": "value"}), "threads", "value", cache_series, "series",
                              f"Cache L{level} {metric} per tx vs threads | ratio={r}% | init_size={pow2_latex(s)}",
                              ratio_dir / f"init_size_{s}_cache_L{level}_{metric}.png",
                              xlabel_override="Threads", ylabel_override=f"L{level} {metric} per tx", show_title=False)

            # Derived metrics (ratios)
            derived = build_cache_derived(sub_r)
            for key, label_text, ddf in derived:
                ylabel = DERIVED_YLABELS.get(key, label_text)
                # By init_size for fixed threads
                for t in THREAD_COUNTS_FOR_SLICE:
                    slice_df = ddf[ddf["threads"] == t].copy()
                    if slice_df.empty: continue
                    raw = slice_df[["init_size", "value", "series"]].drop_duplicates()
                    line_plot(raw, "init_size", "value", cache_series, "series",
                              f"{label_text} vs init_size | ratio={r}% | threads={t}",
                              ratio_dir / f"threads_{t}_cache_{key}.png",
                              xlabel_override="Data structure size", ylabel_override=ylabel, show_title=False)
                # By threads for fixed init_size
                for s in INIT_SIZES_FOR_SLICE:
                    slice_df = ddf[ddf["init_size"] == s].copy()
                    if slice_df.empty: continue
                    raw = slice_df[["threads", "value", "series"]].drop_duplicates()
                    line_plot(raw, "threads", "value", cache_series, "series",
                              f"{label_text} vs threads | ratio={r}% | init_size={pow2_latex(s)}",
                              ratio_dir / f"init_size_{s}_cache_{key}.png",
                              xlabel_override="Threads", ylabel_override=ylabel, show_title=False)

            # === NEW: 3x3 cache grids ===
        cache_grids_dir = outdir / "combined" / "cache_grids"
        ensure_outdir(cache_grids_dir)

        # Use all cache series (union) for consistent colors/markers
        all_cache_series = sorted(cache_df["series"].unique().tolist(), key=str.lower)

        # (A) For each init_size: columns = ratios, rows = {L1 miss, L3 ref, L3 miss}, x-axis = threads
        for s in INIT_SIZES_FOR_SLICE:
            make_cache_3x3_grid(
                cache_df=cache_df, slice_by="init_size", slice_val=s,
                series_list=all_cache_series,
                outfile=cache_grids_dir / f"cache_grid_by_ratio_init_{s}.png"
            )

            make_cache_3x3_grid(
                cache_df=cache_df, slice_by="init_size", slice_val=s,
                series_list=all_cache_series,
                outfile=cache_grids_dir / f"cache_grid_by_ratio_init_{s}_no_legend.png",
                show_legend=False
            )

            make_derived_cache_3x3_grid(
                cache_df     = cache_df,
                slice_by     = 'init_size',
                slice_val    = s,
                series_list  = all_cache_series,
                outfile     = cache_grids_dir / f'cache_derived_grid_by_ratio_init{s}.png'
            )

            make_derived_cache_3x3_grid(
                cache_df     = cache_df,
                slice_by     = 'init_size',
                slice_val    = s,
                series_list  = all_cache_series,
                outfile     = cache_grids_dir / f'cache_derived_grid_by_ratio_init{s}_no_legend.png',
                show_legend=False
            )

        # (B) For each threads: columns = ratios, rows = {L1 miss, L3 ref, L3 miss}, x-axis = init_size
        for t in THREAD_COUNTS_FOR_SLICE:
            make_cache_3x3_grid(
                cache_df=cache_df, slice_by="threads", slice_val=t,
                series_list=all_cache_series,
                outfile=cache_grids_dir / f"cache_grid_by_ratio_threads_{t}.png"
            )

            make_cache_3x3_grid(
                cache_df=cache_df, slice_by="threads", slice_val=t,
                series_list=all_cache_series,
                outfile=cache_grids_dir / f"cache_grid_by_ratio_threads_{t}_no_legend.png",
                show_legend=False
            )

            make_derived_cache_3x3_grid(
                cache_df     = cache_df,
                slice_by     = 'threads',
                slice_val    = t,
                series_list  = all_cache_series,
                outfile     = cache_grids_dir / f'cache_derived_grid_by_ratio_threads{t}.png'
            )

            make_derived_cache_3x3_grid(
                cache_df     = cache_df,
                slice_by     = 'threads',
                slice_val    = t,
                series_list  = all_cache_series,
                outfile     = cache_grids_dir / f'cache_derived_grid_by_ratio_threads{t}_no_legend.png',
                show_legend=False
            )

    # ---------- New: Combined multi-ratio figures ----------
    combined_dir = outdir / "combined"
    ensure_outdir(combined_dir)

    ratios_sorted = sorted(VALID_RATIOS)

    # Prepare series lists (colors/hatches already pre-seeded earlier)
    line_series_all = sorted(df["series"].unique().tolist(), key=str.lower)
    sp_series_all = sorted(df[df["opt"] != "base"]["series"].unique().tolist(), key=str.lower)
    
    l1ref_df = cache_df[
        (cache_df['level'] == 1) & (cache_df['metric'] == 'ref')
    ].copy()

    # a) Throughput lines: for each fixed init_size, vary threads; 3 ratios side-by-side
    for s in INIT_SIZES_FOR_SLICE:
        make_multi_ratio_line(
            df=df, ratios=ratios_sorted,
            slice_by="init_size", slice_val=s,
            x="threads", y="mops",
            series_list=line_series_all, series_col="series",
            outfile=combined_dir / f"tp_threads_all_ratios_init_{s}.png",
            xlabel="Threads", ylabel="Throughput (Mops)",
            title=f"Throughput vs Threads (init_size={pow2_latex(s)})",
            show_baseline=False
        )

        make_multi_ratio_line(
            df=df, ratios=ratios_sorted,
            slice_by="init_size", slice_val=s,
            x="threads", y="mops",
            series_list=line_series_all, series_col="series",
            outfile=combined_dir / f"tp_threads_all_ratios_init_{s}_no_legend.png",
            xlabel="Threads", ylabel="Throughput (Mops)",
            title=f"Throughput vs Threads (init_size={pow2_latex(s)})",
            show_baseline=False, show_legend=False
        )

        make_multi_ratio_line(
            df          = l1ref_df,
            ratios      = ratios_sorted,         
            slice_by     = 'init_size',                   
            slice_val    = s,                           
            x           = 'threads',                  
            y           = 'value',                     
            series_list  = all_cache_series,              
            series_col   = 'series',
            outfile     = combined_dir / f'l1ref_all_ratios_init_{s}.png',
            xlabel      = 'Threads',
            ylabel      = 'L1 refs per tx',
            title       = f'L1 References vs Threads (init_size={pow2_latex(s)}',
            show_baseline= False
        )
        
        make_multi_ratio_line(
            df          = l1ref_df,
            ratios      = ratios_sorted,         
            slice_by     = 'init_size',                   
            slice_val    = s,                           
            x           = 'threads',                  
            y           = 'value',                     
            series_list  = all_cache_series,              
            series_col   = 'series',
            outfile     = combined_dir / f'l1ref_all_ratios_init_{s}_no_legend.png',
            xlabel      = 'Threads',
            ylabel      = 'L1 refs per tx',
            title       = f'L1 References vs Threads (init_size={pow2_latex(s)}',
            show_baseline= False,  show_legend=False
        )

        


    # b) Throughput lines: for each fixed threads, vary init_size; 3 ratios side-by-side
    for t in THREAD_COUNTS_FOR_SLICE:
        # Note: when t==1 you may only have 'sequential' series by design.
        make_multi_ratio_line(
            df=df, ratios=ratios_sorted,
            slice_by="threads", slice_val=t,
            x="init_size", y="mops",
            series_list=line_series_all, series_col="series",
            outfile=combined_dir / f"tp_init_all_ratios_threads_{t}.png",
            xlabel="Data structure size", ylabel="Throughput (Mops)",
            title=f"Throughput vs Initial Size (threads={t})",
            show_baseline=False
        )

        make_multi_ratio_line(
            df=df, ratios=ratios_sorted,
            slice_by="threads", slice_val=t,
            x="init_size", y="mops",
            series_list=line_series_all, series_col="series",
            outfile=combined_dir / f"tp_init_all_ratios_threads_{t}_no_legend.png",
            xlabel="Data structure size", ylabel="Throughput (Mops)",
            title=f"Throughput vs Initial Size (threads={t})",
            show_baseline=False, show_legend=False
        )

        make_multi_ratio_line(
            df          = l1ref_df,
            ratios      = ratios_sorted,         
            slice_by     = 'threads',                   
            slice_val    = t,                           
            x           = 'init_size',                  
            y           = 'value',                     
            series_list  = all_cache_series,              
            series_col   = 'series',
            outfile     = combined_dir / f'l1ref_all_ratios_threads_{t}.png',
            xlabel      = 'Data structure size',
            ylabel      = 'L1 refs per tx',
            title       = f'L1 References vs Initial Size  threads={t}',
            show_baseline= False
        )
        
        make_multi_ratio_line(
            df          = l1ref_df,
            ratios      = ratios_sorted,
            slice_by     = 'threads',                   
            slice_val    = t,                           
            x           = 'init_size',                  
            y           = 'value',                     
            series_list  = all_cache_series,              
            series_col   = 'series',
            outfile     = combined_dir / f'l1ref_all_ratios_threads_{t}_no_legend.png',
            xlabel      = 'Data structure size',
            ylabel      = 'L1 refs per tx',
            title       = f'L1 References vs Initial Size  threads={t}',
            show_baseline= False, show_legend=False
        )

    # Build a full speedup dataframe once (with ratio carried through)
    speed_all = build_speedup(df)
    # c) Speedup bars: for each fixed init_size, vary threads; 3 ratios side-by-side (bars only)
    for s in INIT_SIZES_FOR_SLICE:
        make_multi_ratio_bar(
            speed_df=speed_all, ratios=ratios_sorted,
            slice_by="init_size", slice_val=s,
            x="threads",
            series_list=sp_series_all, series_col="series",
            outfile=combined_dir / f"spbar_threads_all_ratios_init_{s}.png",
            xlabel="Threads", ylabel="Speedup",
            title=f"Speedup vs Threads (init_size={pow2_latex(s)})"
        )

        make_multi_ratio_bar(
            speed_df=speed_all, ratios=ratios_sorted,
            slice_by="init_size", slice_val=s,
            x="threads",
            series_list=sp_series_all, series_col="series",
            outfile=combined_dir / f"spbar_threads_all_ratios_init_{s}_no_legend.png",
            xlabel="Threads", ylabel="Speedup",
            title=f"Speedup vs Threads (init_size={pow2_latex(s)})", show_legend=False
        )

        make_multi_ratio_bar(
            speed_df=speed_all, ratios=ratios_sorted,
            slice_by="init_size", slice_val=s,
            x="threads",
            series_list=sp_series_all, series_col="series",
            outfile=combined_dir / f"spbar_threads_all_ratios_init_{s}_one_line_legend.png",
            xlabel="Threads", ylabel="Speedup",
            title=f"Speedup vs Threads (init_size={pow2_latex(s)})", one_line=True
        )

    # d) Speedup bars: for each fixed threads, vary init_size; 3 ratios side-by-side (bars only)
    for t in THREAD_COUNTS_FOR_SLICE:
        make_multi_ratio_bar(
            speed_df=speed_all, ratios=ratios_sorted,
            slice_by="threads", slice_val=t,
            x="init_size",
            series_list=sp_series_all, series_col="series",
            outfile=combined_dir / f"spbar_init_all_ratios_threads_{t}.png",
            xlabel="Data structure size", ylabel="Speedup",
            title=f"Speedup vs Initial Size (threads={t})"
        )

        make_multi_ratio_bar(
            speed_df=speed_all, ratios=ratios_sorted,
            slice_by="threads", slice_val=t,
            x="init_size",
            series_list=sp_series_all, series_col="series",
            outfile=combined_dir / f"spbar_init_all_ratios_threads_{t}_no_legend.png",
            xlabel="Data structure size", ylabel="Speedup",
            title=f"Speedup vs Initial Size (threads={t})", show_legend=False
        )

        make_multi_ratio_bar(
            speed_df=speed_all, ratios=ratios_sorted,
            slice_by="threads", slice_val=t,
            x="init_size",
            series_list=sp_series_all, series_col="series",
            outfile=combined_dir / f"spbar_init_all_ratios_threads_{t}_one_line_legend.png",
            xlabel="Data structure size", ylabel="Speedup",
            title=f"Speedup vs Initial Size (threads={t})", one_line=True
        )

    print(f"Done. Wrote graphs + legends to: {outdir}")


if __name__ == "__main__": main()


