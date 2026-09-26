import unreal, json
car = unreal.load_asset('/Game/Cara_LiteraLevel')
def volcar(o, prof=0):
    if prof > 3:
        return str(o)
    r = {}
    for p in dir(o):
        if p.startswith('_') or callable(getattr(o, p, None)):
            continue
        try:
            v = o.get_editor_property(p)
        except Exception:
            continue
        if isinstance(v, (int, float, bool, str)):
            r[p] = v
        elif isinstance(v, unreal.StructBase):
            r[p] = volcar(v, prof + 1)
        else:
            r[p] = str(v)[:80]
    return r
out = {k: volcar(car.get_editor_property(k)) for k in ['skin_settings', 'eyes_settings', 'head_model_settings', 'makeup_settings']}
json.dump(out, open('D:/literalevel_cara/ue/ajustes.json', 'w'), indent=1, default=str)
