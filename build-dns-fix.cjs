// DNS patch for offline environments — required because node.exe can't resolve localhost here
const dns = require('node:dns');
const origPLookup = dns.promises.lookup;
dns.promises.lookup = async (hostname, options) => {
  if (hostname === 'localhost' || hostname === 'box') {
    return { address: '127.0.0.1', family: 4 };
  }
  return origPLookup(hostname, options);
};
const origLookup = dns.lookup;
dns.lookup = (hostname, options, callback) => {
  if (typeof options === 'function') { callback = options; options = {}; }
  if (hostname === 'localhost' || hostname === 'box') {
    if (typeof callback === 'function') return callback(null, '127.0.0.1', 4);
    return { address: '127.0.0.1', family: 4 };
  }
  return origLookup(hostname, options, callback);
};

// Fix process.argv for astro
process.argv = [process.argv[0], __filename, ...process.argv.slice(2)];
require('./node_modules/astro/astro.js');
