const fs = require('fs');
const path = require('path');

function scanDistPages(dist) {
  const pages = [];
  function walk(dir) {
    const entries = fs.readdirSync(dir, {withFileTypes: true});
    for (const e of entries) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) {
        const rel = path.relative(dist, p);
        if (rel.startsWith('_astro') || rel.startsWith('assets')) continue;
        walk(p);
      } else if (e.name.endsWith('.html') || e.name.endsWith('.htm')) {
        pages.push(p);
      }
    }
  }
  walk(dist);
  return pages;
}

const all = scanDistPages('dist');
const exclude = ['/404.', '/500.', '/admin/', '/dashboard/', '/login/', '/assets/', '/_astro/', '/node_modules/'];
const articles = all.filter(function(p) {
  var norm = p.replace(/\\/g, '/');
  return !exclude.some(function(x) { return norm.includes(x); });
});

console.log('Total HTML pages: ' + all.length);
console.log('Content pages (after Gremium filter): ' + articles.length);
console.log('');
console.log('First 20 pages tested by Gremium:');
articles.slice(0,20).forEach(function(p,i) {
  var rel = path.relative('dist', p);
  var html = fs.readFileSync(p, 'utf8');
  var hasAmazon = html.includes('tag=nova079-20');
  var hasMeta = html.includes('<meta name="description"') || html.includes('<meta name="Description"');
  var hasJsonld = html.includes('"@type"') && (html.includes('"BlogPosting"') || html.includes('"WebPage"') || html.includes('"Article"') || html.includes('"WebSite"'));
  console.log('' + (i+1) + '. ' + rel + ' | Amazon:' + hasAmazon + ' Meta:' + hasMeta + ' JSON-LD:' + hasJsonld);
});

console.log('');
// Summary
var amazonCount = 0, metaCount = 0, jsonldCount = 0;
articles.slice(0,20).forEach(function(p) {
  var html = fs.readFileSync(p, 'utf8');
  if (html.includes('tag=nova079-20')) amazonCount++;
  if (html.includes('<meta name="description"') || html.includes('<meta name="Description"')) metaCount++;
  if (html.includes('"@type"') && (html.includes('"BlogPosting"') || html.includes('"WebPage"') || html.includes('"Article"') || html.includes('"WebSite"'))) jsonldCount++;
});
console.log('SUMMARY for first 20:');
console.log('Amazon links: ' + amazonCount + '/20');
console.log('Meta descriptions: ' + metaCount + '/20');
console.log('JSON-LD: ' + jsonldCount + '/20');
