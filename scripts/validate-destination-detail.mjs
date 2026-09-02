import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const slugs = ["leptis-magna", "tripoli", "acacus", "sabratha", "ghadames", "awjila", "ras-al-hilal"];
const context = { window: {} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(root, "assets/js/data/destination-details.js"), "utf8"), context);
const records = context.window.VISITLIBYA_DESTINATION_DETAILS;
const errors = [];

function count(source, expression) {
  return [...source.matchAll(expression)].length;
}

for (const arabic of [false, true]) {
  for (const slug of slugs) {
    const relative = `${arabic ? "ar/" : ""}destinations/${slug}.html`;
    const file = path.join(root, relative);
    const source = fs.readFileSync(file, "utf8");
    for (const [label, expression] of [
      ["DOCTYPE", /<!doctype html>/gi], ["html element", /<html\b/gi],
      ["head", /<head\b/gi], ["body", /<body\b/gi], ["h1", /<h1\b/gi],
    ]) if (count(source, expression) !== 1) errors.push(`${relative}: expected exactly one ${label}`);
    const language = arabic ? "ar" : "en";
    const direction = arabic ? "rtl" : "ltr";
    if (!new RegExp(`<html[^>]+lang=["']${language}["'][^>]+dir=["']${direction}["']`, "i").test(source)) errors.push(`${relative}: invalid lang/dir`);
    if (!source.includes(`data-destination="${slug}"`) || !records[slug]) errors.push(`${relative}: destination record mismatch`);
    for (const match of source.matchAll(/(?:href|src)=["']([^"']+)["']/gi)) {
      const reference = match[1].split(/[?#]/, 1)[0];
      if (!reference || reference.startsWith("#") || /^[a-z][a-z0-9+.-]*:/i.test(reference)) continue;
      if (reference.startsWith("/")) { errors.push(`${relative}: root-relative reference ${reference}`); continue; }
      const target = path.resolve(path.dirname(file), decodeURIComponent(reference));
      if (!fs.existsSync(target)) errors.push(`${relative}: missing reference ${reference}`);
    }
  }
}

const imagePaths = new Set();
for (const [slug, record] of Object.entries(records)) {
  const images = [record.hero, record.introduction.image, ...record.highlights.map((item) => item.image), record.visualStory.image, record.context.image, ...record.gallery, record.atlas.image];
  for (const image of images) {
    const relative = decodeURI(image.src.replace(/^\.\.\//, ""));
    imagePaths.add(relative);
    if (!fs.existsSync(path.join(root, relative))) errors.push(`${slug}: missing image ${relative}`);
  }
}

if (imagePaths.has("liptes-contact-sheet.jpg") || [...imagePaths].some((item) => item.endsWith("/liptes-contact-sheet.jpg"))) errors.push("contact sheet is referenced");
if (errors.length) {
  console.error(errors.map((error) => `FAIL ${error}`).join("\n"));
  process.exitCode = 1;
} else {
  console.log(`PASS 14 destination shells, ${slugs.length} shared records, ${imagePaths.size} exact image references`);
}
