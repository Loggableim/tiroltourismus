// Patch DNS promises for localhost
const dns = require('dns');
const dnsPromises = dns.promises;

const originalLookup = dnsPromises.lookup;
dnsPromises.lookup = function(hostname, options) {
  if (hostname === 'localhost' || hostname === 'localhost.') {
    return Promise.resolve({ address: '127.0.0.1', family: 4 });
  }
  return originalLookup.call(this, hostname, options);
};

// Also patch callback-based lookup
const origLookupCb = dns.lookup;
const origLookupAll = dns.lookup.__original_lookup_all;
dns.lookup = function(hostname, options, callback) {
  if (hostname === 'localhost' || hostname === 'localhost.') {
    if (typeof options === 'function') {
      callback = options;
      options = {};
    }
    if (typeof options === 'object' && options.all) {
      setImmediate(() => callback(null, [{ address: '127.0.0.1', family: 4 }]));
      return {};
    }
    setImmediate(() => callback(null, '127.0.0.1', 4));
    return {};
  }
  if (typeof options === 'function') {
    return origLookupCb(hostname, options);
  }
  return origLookupCb(hostname, options, callback);
};

// Also try to override dns.resolve/dns.resolve4
const origResolve = dns.resolve;
dns.resolve = function(hostname, rrtype, callback) {
  if (hostname === 'localhost') {
    if (typeof rrtype === 'function') {
      callback = rrtype;
      rrtype = 'A';
    }
    setImmediate(() => callback(null, ['127.0.0.1']));
    return {};
  }
  if (typeof rrtype === 'function') {
    return origResolve(hostname, rrtype);
  }
  return origResolve(hostname, rrtype, callback);
};

const origResolve4 = dns.resolve4;
dns.resolve4 = function(hostname, options, callback) {
  if (hostname === 'localhost') {
    if (typeof options === 'function') {
      callback = options;
      options = {};
    }
    setImmediate(() => callback(null, ['127.0.0.1']));
    return {};
  }
  if (typeof options === 'function') {
    return origResolve4(hostname, options);
  }
  return origResolve4(hostname, options, callback);
};

// Promises versions
const promResolve = dnsPromises.resolve;
dnsPromises.resolve = function(hostname, rrtype) {
  if (hostname === 'localhost') {
    return Promise.resolve(['127.0.0.1']);
  }
  return promResolve.call(this, hostname, rrtype);
};

const promResolve4 = dnsPromises.resolve4;
dnsPromises.resolve4 = function(hostname, options) {
  if (hostname === 'localhost') {
    return Promise.resolve(['127.0.0.1']);
  }
  return promResolve4.call(this, hostname, options);
};

console.log('[dns-fix] DNS overrides installed for localhost');
