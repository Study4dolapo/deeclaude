"""Assemble standalone image prompts for every script beat.

Data files in data/*.txt use one line per entry:
  @ <segment title> | <location/environment context>
  <beat id> | <subject + scene> | <camera code> | <lighting code> | <mood> | <action>
A subject starting with "!" skips the segment context prefix.
"""
import csv, glob, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
STYLE = ("Earth Uncharted Cinematic style: photorealistic cinematic documentary still, "
         "shot on a professional drone and cinema camera, 8K, ultra-detailed, vivid natural colors, "
         "deep depth of field, atmospheric haze, dramatic natural lighting, epic sense of scale, "
         "National Geographic quality, no text, no watermark")

CAMERA = {
    "AH": "high-altitude aerial drone shot looking down across the whole landscape",
    "AO": "45-degree oblique aerial drone shot",
    "TD": "top-down overhead drone shot",
    "OR": "slow orbiting aerial drone shot around the subject",
    "PI": "slow aerial push-in toward the subject",
    "LA": "low-altitude drone shot skimming just above the surface",
    "GW": "ground-level wide shot, 24mm lens",
    "LO": "low-angle ground shot looking up, 24mm lens",
    "EL": "eye-level medium shot, 35mm lens",
    "LL": "long-lens telephoto shot, 200mm compression",
    "CU": "close-up detail shot, 100mm macro lens",
    "UW": "underwater wide shot, 16mm lens",
    "SP": "orbital view from space looking down at Earth",
}
LIGHT = {
    "GH": "warm golden-hour side light with long shadows",
    "SB": "bright high midday sun with crisp shadows",
    "BL": "backlit sun with glowing rim light and gentle lens flare",
    "OV": "soft diffused overcast light",
    "FG": "soft light filtered through drifting fog and mist",
    "NT": "deep blue night with moonlight",
    "DU": "blue-hour dusk light with a fading orange horizon",
    "DW": "cool pale dawn light with low mist",
    "GL": "intense orange practical glow from fire and molten rock against darkness",
    "ST": "dark stormy light with heavy clouds and shafts of sun",
    "UL": "shafts of sunlight piercing through water from above",
    "DK": "near-total darkness lit only by a single headlamp beam",
    "SN": "bright cold light reflecting off snow and ice",
}

def load():
    seg_env, rows = {}, []
    cur = None
    for path in sorted(glob.glob(os.path.join(HERE, "data", "*.txt"))):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@"):
                title, env = [p.strip() for p in line[1:].split("|", 1)]
                seg_env[title] = env
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 6:
                raise SystemExit(f"{path}: bad line: {line}")
            rows.append(parts)
    return seg_env, {int(r[0]): r for r in rows}

def main():
    beats = json.load(open(os.path.join(HERE, "beats.json"), encoding="utf-8"))
    seg_env, rows = load()
    missing = [b["id"] for b in beats if b["id"] not in rows]
    md = ["# EARTH'S DEADLIEST PLACES — Image Prompts (STATE 8)", "",
          f"*{len(beats)} beats, each max 3–5 seconds of narration. Every prompt is standalone and follows the Earth Uncharted Cinematic Visual Style Profile.*", ""]
    out_rows, cur_seg = [], None
    for b in beats:
        r = rows.get(b["id"])
        if not r:
            continue
        _, subj, cam, lig, mood, action = r
        cam_t, lig_t = CAMERA.get(cam, cam), LIGHT.get(lig, lig)
        if subj.startswith("!"):
            scene = subj[1:].strip()
        else:
            scene = f"{seg_env[b['seg']]}. {subj}"
        prompt = f"{scene}. {cam_t[0].upper() + cam_t[1:]}, {lig_t}, {mood} mood. {STYLE}."
        prompt = re.sub(r"\.\.", ".", prompt)
        if b["seg"] != cur_seg:
            cur_seg = b["seg"]
            md += [f"## {cur_seg}", ""]
        md += [f"### Beat {b['id']:04d}",
               f"**[Script Segment Text]** \"{b['text']}\"", "",
               f"**Image Prompt:** {prompt}", "",
               f"- **Camera Angle:** {cam_t}",
               f"- **Lighting:** {lig_t}",
               f"- **Mood:** {mood}",
               f"- **Action:** {action}", ""]
        out_rows.append([b["id"], b["seg"], b["text"], prompt, cam_t, lig_t, mood, action])
    open(os.path.join(HERE, "earths-deadliest-places-image-prompts.md"), "w", encoding="utf-8").write("\n".join(md))
    with open(os.path.join(HERE, "earths-deadliest-places-image-prompts.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["beat", "segment", "script_text", "image_prompt", "camera_angle", "lighting", "mood", "action"])
        w.writerows(out_rows)
    print(f"{len(out_rows)} prompts written; {len(missing)} beats missing" + (f" (first: {missing[:10]})" if missing else ""))

if __name__ == "__main__":
    main()
