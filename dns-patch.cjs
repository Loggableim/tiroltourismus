// Preload script to fix DNS resolution for localhost
const dns = require('dns');
const originalLookup = dns.lookup;
dns.lookup = function(hostname, options, callback) {
  if (typeof options === 'function') {
    callback = options;
    options = {};
  }
  if (hostname === 'localhost' || hostname === 'LOCALHOST') {
    if (typeof callback === 'function') {
      callback(null, '127.0.0.1', 4);
    }
    return;
  }
  return originalLookup.call(dns, hostname, options, callback);
};

// Also patch promises API
if (dns.promises && dns.promises.lookup) {
  const origPromiseLookup = dns.promises.lookup;
  dns.promises.lookup = function(hostname, options) {
    if (hostname === 'localhost' || hostname === 'LOCALHOST') {
      return Promise.resolve({ address: '127.0.0.1', family: 4 });
    }
    return origPromiseLookup.call(dns.promises, hostname, options);
  };
}

console.log('[dns-patch] localhost DNS resolution patched');
