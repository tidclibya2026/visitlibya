# Visit Libya – Phase 3: Media + Arabic

This patch adds:

1. YouTube videos connected through `site-content.js`:
   - https://youtu.be/-KW6pQcq-LI
   - https://youtu.be/XFS_h8s8www
   - https://youtu.be/YZnbQtQRLgo
   - https://youtu.be/SF6Ou54SFdo

2. GitHub-linked content source:
   - Videos and gallery images are controlled from `site-content.js`.
   - Local images still use the existing `imges/` folder.
   - To update videos or images, edit `site-content.js` only.

3. Arabic language support:
   - The language button toggles between English and Arabic.
   - The selected language is saved in localStorage.
   - The site switches `html lang` and `dir` automatically.

Install:
Copy all files into the project root and keep the current `imges` folder.
