import json

with open("C:/mcp-agent/current.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total original sections: {len(data)}\n")
for i, s in enumerate(data):
    bg = s['settings'].get('background_color', s['settings'].get('background_background',''))
    # Get widget types in this section
    widgets = []
    for col in s.get('elements', []):
        for el in col.get('elements', []):
            wt = el.get('widgetType', el.get('elType',''))
            if wt:
                # Get title/text preview
                sets = el.get('settings', {})
                preview = sets.get('title', sets.get('editor',''))[:50] if sets else ''
                widgets.append(f"{wt}: {preview[:40]}")
            # Check inner elements
            for inner in el.get('elements', []):
                wt2 = inner.get('widgetType','')
                if wt2:
                    sets2 = inner.get('settings',{})
                    preview2 = sets2.get('title', sets2.get('editor',''))[:40] if sets2 else ''
                    widgets.append(f"  {wt2}: {preview2[:35]}")

    print(f"Section {i} (id={s['id']}):")
    print(f"  BG: {bg}")
    print(f"  Widgets: {'; '.join(widgets[:5])}")
    print()
