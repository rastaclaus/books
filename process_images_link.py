"""process media"""

import re
from urllib.error import HTTPError
from urllib.request import urlretrieve
from pathlib import Path

from PIL import Image

IMGREF = re.compile(r'(\\includegraphics\{(.+?)\})')
MEDIA = 'media'
REPLACEMENT = "\\includegraphics[width=\\textwidth, natwidth={}, natheight={}]{{{}}}"


def main():
    """entry point"""
    media = Path(MEDIA)

    media.mkdir(exist_ok=True)
    with open('content.tex') as texfile, open('content_processed.tex', 'w') as newtex:
        for line in texfile:
            refs = IMGREF.findall(line)
            for ref in refs:
                imgfile = ref[1].split('/')[-1]
                try:
                    if not (media/imgfile).exists():
                        urlretrieve(ref[1], str(media/imgfile))
                except HTTPError:
                    print(line)
                    print(ref[1])
                    line = ""
                image = Image.open(str(media/imgfile))
                width, height = image.size
                repl = REPLACEMENT.format(width, height, str(media/imgfile))
                print(repl)
                line = line.replace(ref[0], repl)
            newtex.write(line)

if __name__ == '__main__':
    main()
