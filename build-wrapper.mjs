import { lookup, lookupService } from 'dns';

const origLookup = lookup;
const origLookupService = lookupService;

// Override dns.lookup to handle localhost resolution failure
const dnsModule = require('dns');
dnsModule.lookup = (hostname, options, callback) => {
  if (typeof options === 'function') { callback = options; options = {}; }
  if (hostname === 'localhost' || hostname === 'box') {
    if (typeof callback === 'function') {
      return callback(null, '127.0.0.1', 4);
    }
    return origLookup(hostname, { ...options, hints: 0 }, callback);
  }
  return origLookup(hostname, options, callback);
};

dnsModule.lookupService = (address, port, callback) => {
  if (address === '127.0.0.1') {
    if (typeof callback === 'function') {
      return callback(null, 'localhost', 0);
    }
    return origLookupService(address, port, callback);
  }
  return origLookupService(address, port, callback);
};

import('./node_modules/astro/astro.js');
