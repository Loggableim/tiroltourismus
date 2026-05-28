#!/bin/bash
# DNS-fixed Astro build wrapper for tiroltourismus
# Workaround: node:dns can't resolve localhost in this isolated environment
export PATH="/c/Users/logga/AppData/Local/Temp/node20/node-v20.19.1-win-x64:$PATH"
cd F:/tiroltourismus || exit 1

# Clean previous partial build
rm -rf dist

# Run with DNS patching
NODE_OPTIONS="--max-old-space-size=4096" node -e "
process.argv = [process.argv[0], './node_modules/astro/astro.js', 'build'];
import('dns').then(dns => {
  dns.default.promises.lookup = async (hostname) => {
    if (hostname === 'localhost' || hostname === 'box') return { address: '127.0.0.1', family: 4 };
    return dns.default.promises.lookup(hostname);
  };
  dns.default.lookup = (hostname, options, callback) => {
    if (typeof options === 'function') { callback = options; options = {}; }
    if (hostname === 'localhost' || hostname === 'box') {
      if (typeof callback === 'function') return callback(null, '127.0.0.1', 4);
      return { address: '127.0.0.1', family: 4 };
    }
    return dns.default.lookup(hostname, options, callback);
  };
  return import('./node_modules/astro/astro.js');
}).catch(e => { console.error('Build error:', e); process.exit(1); });
" 2>&1
echo "EXIT_CODE=$?"
