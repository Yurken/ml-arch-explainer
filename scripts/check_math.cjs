const fs = require('node:fs');
const katex = require('../assets/vendor/katex/katex.min.js');
const {format} = require('../assets/math.js')(katex);
const skip = new Set(['id','source','target','node_ids','focus_node','active_nodes','active_edges',
  'url','verified','pseudocode','dtype','category','color','phase','default_layout','kind','type','relation']);
function check(value, key, path) {
  if (skip.has(key)) return;
  if (typeof value === 'string') {
    const mode = key === 'formula_latex' ? 'display' : ['symbol','shape','tensor_shape'].includes(key) ? 'symbol' : 'text';
    try {
      if (key === 'formula_latex' && /[\x00-\x08\x0b\x0c\x0e-\x1f]/.test(value)) throw Error('Unexpected control character');
      format(value, mode);
    } catch (error) {throw Error(path + ': ' + error.message)}
  } else if (Array.isArray(value)) {
    value.forEach((item,i) => check(item,key,path+'['+i+']'));
  } else if (value && typeof value === 'object') {
    for (const [field,item] of Object.entries(value)) check(item,field,path+'.'+field);
  }
}
try {check(JSON.parse(fs.readFileSync(0,'utf8')),'','data')}
catch (error) {console.error(error.message);process.exitCode=1}
