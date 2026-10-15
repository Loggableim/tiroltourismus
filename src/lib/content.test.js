import test from 'node:test';
import assert from 'node:assert/strict';
import { autoLinkContent, stripDescriptionSectionMarkers } from './content.js';

test('removes a standalone description marker before plain text', () => {
  assert.equal(
    stripDescriptionSectionMarkers('=== beschreibung ===\nA family-run hotel in Tirol.'),
    'A family-run hotel in Tirol.',
  );
});

test('removes a description marker between HTML blocks without changing the copy', () => {
  assert.equal(
    stripDescriptionSectionMarkers('<p>Overview</p><br><br>=== beschreibung ===<br><p>Details</p>'),
    '<p>Overview</p><br><br><br><p>Details</p>',
  );
});

test('removes a description marker wrapped in its own paragraph', () => {
  assert.equal(
    stripDescriptionSectionMarkers('<p>=== beschreibung ===</p><p>Details</p>'),
    '<p>Details</p>',
  );
});

test('preserves inline prose that mentions the marker text', () => {
  assert.equal(
    stripDescriptionSectionMarkers('The literal === beschreibung === marker is discussed here.'),
    'The literal === beschreibung === marker is discussed here.',
  );
});

test('cleans field markers before the detail-page link renderer runs', () => {
  assert.equal(
    autoLinkContent('=== beschreibung ===<br><p>Breakfast included.</p>', {}, 'en', 5, 'unterkuenfte', 'basic-hotel'),
    '<p>Breakfast included.</p>',
  );
});
