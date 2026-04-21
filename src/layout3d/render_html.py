"""HTML-Ausgabe für Layer-PNG-Galerien."""

from __future__ import annotations

from html import escape
from os.path import relpath
from pathlib import Path


def write_layer_gallery_html(
    out_html: Path,
    png_files: list[Path],
    title: str = "Layout-Layer",
) -> None:
    sections: list[str] = []
    for layer_idx, png_file in enumerate(png_files):
        rel_src = Path(relpath(png_file.resolve(), start=out_html.parent.resolve()))
        src = escape(rel_src.as_posix(), quote=True)
        sections.append(
            f"""
    <section class="layer">
      <h2>Layer {layer_idx}</h2>
      <img src="{src}" alt="Layer {layer_idx}" loading="lazy">
    </section>""".rstrip()
        )

    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <style>
      :root {{ color-scheme: light dark; }}
      body {{
        font-family: system-ui, sans-serif;
        margin: 1rem auto;
        max-width: 1200px;
        padding: 0 1rem 2rem;
      }}
      img {{
        cursor: zoom-in;
        display: block;
        height: auto;
        max-width: 100%;
      }}
      .layer {{ margin: 0 0 1.5rem; }}
      #overlay {{
        align-items: center;
        background: rgba(0, 0, 0, 0.8);
        cursor: zoom-out;
        display: none;
        inset: 0;
        justify-content: center;
        position: fixed;
      }}
      #overlay[aria-hidden="false"] {{ display: flex; }}
      #overlay img {{
        cursor: default;
        max-height: 90vh;
        max-width: 95vw;
      }}
      #overlay button {{
        background: transparent;
        border: none;
        color: white;
        cursor: pointer;
        font-size: 2rem;
        position: absolute;
        right: 1rem;
        top: 0.5rem;
      }}
    </style>
  </head>
  <body>
    <h1>{escape(title)}</h1>
{chr(10).join(sections)}
    <div id="overlay" aria-hidden="true">
      <button type="button" id="overlay-close" aria-label="Close">&times;</button>
      <img id="overlay-image" alt="">
    </div>
    <script>
      const overlay = document.getElementById("overlay");
      const overlayImage = document.getElementById("overlay-image");
      const closeButton = document.getElementById("overlay-close");
      const layerImages = document.querySelectorAll("section.layer img");

      function closeOverlay() {{
        overlay.setAttribute("aria-hidden", "true");
        overlayImage.removeAttribute("src");
      }}

      layerImages.forEach((img) => {{
        img.addEventListener("click", () => {{
          overlayImage.setAttribute("src", img.getAttribute("src"));
          overlay.setAttribute("aria-hidden", "false");
        }});
      }});

      closeButton.addEventListener("click", closeOverlay);
      overlay.addEventListener("click", (event) => {{
        if (event.target === overlay) {{
          closeOverlay();
        }}
      }});
      document.addEventListener("keydown", (event) => {{
        if (event.key === "Escape" && overlay.getAttribute("aria-hidden") === "false") {{
          closeOverlay();
        }}
      }});
    </script>
  </body>
</html>
"""
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(html, encoding="utf-8")
