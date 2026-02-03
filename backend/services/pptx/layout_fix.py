from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.slide import Slide


def fix_title_overlap(slide: Slide) -> None:  # noqa: C901
    try:
        title_shape = slide.shapes.title if slide.shapes.title else None
        if not title_shape:
            sorted_shapes = sorted(
                [s for s in slide.shapes if s.has_text_frame],
                key=lambda s: s.top,
            )
            if sorted_shapes:
                title_shape = sorted_shapes[0]

        if not title_shape:
            return

        margin_buffer = 50000
        title_bottom = title_shape.top + title_shape.height + margin_buffer
        slide_height = getattr(
            slide.part.presentation,
            "slide_height",
            6858000,
        )

        valid_types = (
            MSO_SHAPE_TYPE.PICTURE,
            MSO_SHAPE_TYPE.GROUP,
            MSO_SHAPE_TYPE.TABLE,
            MSO_SHAPE_TYPE.AUTO_SHAPE,
        )

        obstacles = [
            s
            for s in slide.shapes
            if s.shape_id != title_shape.shape_id
            and s.shape_type in valid_types
        ]

        if not obstacles:
            return

        columns = []
        sorted_obs = sorted(obstacles, key=lambda s: s.left)

        while sorted_obs:
            current = sorted_obs.pop(0)
            col = [current]
            remaining = []

            for other in sorted_obs:
                overlap_x = (
                    min(
                        current.left + current.width,
                        other.left + other.width,
                    )
                    - max(current.left, other.left)
                )
                is_aligned = False

                if overlap_x > 0:
                    share_pct = overlap_x / min(
                        current.width,
                        other.width,
                    )
                    if share_pct > 0.5:
                        is_aligned = True

                if is_aligned:
                    col.append(other)
                else:
                    remaining.append(other)

            columns.append(col)
            sorted_obs = remaining

        for col in columns:
            col.sort(key=lambda s: s.top)

            col_top = col[0].top
            col_bottom = col[-1].top + col[-1].height

            if col_top < title_bottom and col_bottom > title_shape.top:
                limit_bottom = slide_height
                col_ids = {s.shape_id for s in col}
                c_left = min(s.left for s in col)
                c_width = max(s.left + s.width for s in col) - c_left

                for potential in slide.shapes:
                    if potential.shape_id in col_ids:
                        continue
                    if potential.shape_id == title_shape.shape_id:
                        continue

                    if potential.top >= col_top:
                        p_overlap = (
                            min(
                                c_left + c_width,
                                potential.left + potential.width,
                            )
                            - max(c_left, potential.left)
                        )
                        if p_overlap > 0 and potential.top < limit_bottom:
                            limit_bottom = potential.top

                margin = 50000
                target_top = title_bottom + margin
                max_frame_height = (limit_bottom - margin) - target_top

                if max_frame_height < 100000:
                    continue

                current_group_height = col_bottom - col_top
                scale = (
                    max_frame_height / current_group_height
                    if current_group_height > max_frame_height
                    else 1.0
                )

                base_top = target_top
                for shape in col:
                    rel_y = shape.top - col_top
                    new_rel_y = int(rel_y * scale)
                    shape.top = base_top + new_rel_y
                    shape.height = int(shape.height * scale)
                    shape.width = int(shape.width * scale)

    except Exception as exc:
        print(f"[LAYOUT_FIX] Error in fix_title_overlap: {exc}", flush=True)
