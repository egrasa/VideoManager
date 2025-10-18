#!/usr/bin/env python3
"""Quick test of grid layout calculation."""

# Simulate width calculations
def calculate_cols(available_width):
    """ calculate number of columns based on available width """
    usable_width = available_width - 30
    column_width = 160 + 10  # thumbnail + spacing
    calculated_cols = max(1, usable_width // column_width)

    grid_cols = {400: 1, 600: 2, 900: 3, 1600: 4}
    max_cols = 4
    for threshold, col_count in sorted(grid_cols.items()):
        if available_width >= threshold:
            max_cols = col_count

    final_colms = min(calculated_cols, max_cols)
    return final_colms, usable_width, column_width

# Test different widths
test_widths = [300, 400, 600, 800, 900, 1000, 1200, 1600, 1800]

print("Width Analysis for Grid Columns")
print("=" * 70)
print(f"{'Window Width':<15} {'Usable':<12} {'Calculated':<15} {'Final Cols':<12}")
print("-" * 70)

for width in test_widths:
    final_cols, usable, col_width = calculate_cols(width)
    calculated = usable // col_width
    print(f"{width:<15} {usable:<12} {calculated:<15} {final_cols:<12}")

print("-" * 70)
print("\nNote: Column width = 160px (thumbnail) + 10px (spacing) = 170px")
print("Scrollbar + margins = 30px")
print("Breakpoints: 400->1, 600->2, 900->3, 1600->4 columns max")
