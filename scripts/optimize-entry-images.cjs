// Format/size optimization only: original user-supplied photographs remain untouched.
const sharp = require('sharp');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'frontend', 'assets');
fs.mkdirSync(output, {recursive:true});
(async()=>{
  for (const [number,name] of [[1,'map'],[2,'analysis'],[3,'communities'],[4,'surveillance'],[5,'protection']]) {
    const filename = `${number > 3 ? 'Image' : 'image'} ${number}.jpg`;
    await sharp(path.join(root,'images',filename)).rotate().resize({width:1920,height:1920,fit:'inside',withoutEnlargement:true}).webp({quality:78}).toFile(path.join(output,`entry-${name}.webp`));
  }
})();
