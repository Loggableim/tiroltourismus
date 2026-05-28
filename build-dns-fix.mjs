import { lookup, promises } from 'node:dns';
import { createRequire } from 'node:module';

// Patch dns.lookup
const origLookup = lookup;
const dnsModule = await import('node:dns');
const dns = dnsModule.default || dnsModule;
dns.lookup = (hostname, options, callback) => {
  if (typeof options === 'function') { callback = options; options = {}; }
  if (hostname === 'localhost' || hostname === 'box') {
    if (typeof callback === 'function') return callback(null, '127.0.0.1', 4);
    return { address: '127.0.0.1', family: 4 };
  }
  return origLookup(hostname, options, callback);
};

// Patch dns.promises.lookup
const origPromisesLookup = promises.lookup;
dns.promises.lookup = async (hostname, options) => {
  if (hostname === 'localhost' || hostname === 'box') {
    return { address: '127.0.0.1', family: 4 };
  }
  return origPromisesLookup(hostname, options);
};

// Patch lookupService
const origLookupService = dns.lookupService;
dns.lookupService = (address, port, callback) => {
  if (address === '127.0.0.1' && typeof callback === 'function') {
    return callback(null, 'localhost', port);
  }
  return origLookupService(address, port, callback);
};

const origPromisesLookupService = promises.lookupService;
dns.promises.lookupService = async (address, port) => {
  if (address === '127.0.0.1') {
    return { hostname: 'localhost', service: port };
  }
  return origPromisesLookupService(address, port);
};

// Also patch module-level dns
process.env.NODE_OPTIONS = process.env.NODE_OPTIONS || '';
if (!process.env.NODE_OPTIONS.includes('--stack-trace')) {
  process.env.NODE_OPTIONS += ' --stack-trace-limit=100';
}

// Now import Astro
const { execPath } = process;
const require = createRequire(import.meta.url);
console.error('[dns-fix] Patched, starting astro build...');
await import('./node_modules/astro/astro.js');
