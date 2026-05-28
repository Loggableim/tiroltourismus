// DNS patch for offline environments where localhost can't be resolved
const dns = require('node:dns');
const origLookup = dns.lookup;
dns.lookup = (hostname, options, callback) => {
  if (typeof options === 'function') { callback = options; options = {}; }
  const isFn = typeof callback === 'function';
  if (hostname === 'localhost' || hostname === 'box') {
    const isAll = options && options.all;
    const family = options && options.family ? options.family : 4;
    if (isAll) {
      if (isFn) return callback(null, [{ address: '127.0.0.1', family: 4 }]);
      return [{ address: '127.0.0.1', family: 4 }];
    }
    if (isFn) return callback(null, '127.0.0.1', 4);
    return { address: '127.0.0.1', family: 4 };
  }
  return origLookup(hostname, options, callback);
};

const origLookupService = dns.lookupService;
dns.lookupService = (address, port, callback) => {
  if (address === '127.0.0.1' && typeof callback === 'function') {
    return callback(null, 'localhost', port);
  }
  return origLookupService(address, port, callback);
};

delete require.cache[require.resolve('node:dns')];
require('./node_modules/astro/astro.js');
