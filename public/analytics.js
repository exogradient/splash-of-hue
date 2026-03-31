// ============================================================
// splash-of-hue analytics — SINGLE SOURCE OF TRUTH
// ============================================================
// This file defines EVERY event that leaves the client.
// Grep this file to audit telemetry. Nothing else sends data.
//
// Privacy guarantees:
//   - No PII (no email, name, IP, user agent, device fingerprint)
//   - No cookies or persistent identifiers
//   - Autocapture, session recording, pageview capture: OFF
//   - PostHog $ip processing: disabled server-side
//   - All events are explicitly defined below
// ============================================================

(function () {
  'use strict';

  // --- PostHog init (privacy-safe) ---
  // API key is a write-only client token — can ingest events, cannot read data.
  var PH_KEY = 'phc_knK62rpB1yFgSOJgWUVjDslP3PIfwqea5LnzK72gaBQ';
  var PH_HOST = 'https://us.i.posthog.com';

  if (typeof posthog !== 'undefined') {
    posthog.init(PH_KEY, {
      api_host: PH_HOST,
      autocapture: false,
      capture_pageview: false,
      capture_pageleave: false,
      disable_session_recording: true,
      disable_surveys: true,
      ip: false,
      property_denylist: ['$ip'],
      persistence: 'memory',
      advanced_disable_decide: true,
    });
  }

  // --- Private state ---
  var _sessionGameCount = 0;
  var _gameStartedAt = null;
  var _memorizeStartedAt = null;
  var _pickStartedAt = null;
  var _pickerAdjustments = 0;
  var _previousMode = null;
  var _inProgress = false;

  // --- Helpers ---

  function viewportBucket() {
    var w = window.innerWidth;
    if (w < 768) return 'mobile';
    if (w <= 1024) return 'tablet';
    return 'desktop';
  }

  function capture(eventName, props) {
    if (typeof posthog !== 'undefined' && typeof posthog.capture === 'function') {
      try { posthog.capture(eventName, props); } catch (e) { /* silent */ }
    }
  }

  // --- Event schema (inline documentation) ---
  //
  // session_started     : page load — viewport info
  // game_started        : new game begins — mode, picker, session count
  // mode_transition     : player switched modes between games
  // memorize_started    : memorize phase begins (play mode only) — timing anchor
  // pick_started        : pick phase begins — timing anchor
  // round_completed     : one color scored — deltas, timing, interactions,
  //                       call_chosen_name/call_correct_name (call mode only)
  // game_completed      : all 5 rounds done — aggregate score, duration
  // game_abandoned      : left mid-game — how far they got
  // picker_switched     : changed picker type — during game or from menu

  // --- Public API ---

  window.analytics = {

    sessionStarted: function () {
      capture('session_started', {
        viewport_bucket: viewportBucket(),
      });
    },

    gameStarted: function (mode, pickerType) {
      _gameStartedAt = Date.now();
      _pickerAdjustments = 0;
      _inProgress = true;

      // Detect mode transition
      if (_previousMode !== null && _previousMode !== mode) {
        capture('mode_transition', {
          from_mode: _previousMode,
          to_mode: mode,
        });
      }

      capture('game_started', {
        mode: mode,
        picker_type: (mode === 'picture' || mode === 'call') ? 'none' : pickerType,
        viewport_bucket: viewportBucket(),
        session_game_index: _sessionGameCount,
      });

      _sessionGameCount++;
      _previousMode = mode;
    },

    memorizeStarted: function () {
      _memorizeStartedAt = Date.now();
    },

    pickStarted: function () {
      _pickStartedAt = Date.now();
      _pickerAdjustments = 0;
    },

    pickerAdjusted: function () {
      _pickerAdjustments++;
    },

    roundCompleted: function (roundIndex, result, mode, pickerType, selectedChoiceIndex, correctChoiceIndex, callChosenName, callCorrectName) {
      var now = Date.now();
      capture('round_completed', {
        mode: mode,
        picker_type: pickerType,
        round_index: roundIndex,
        score: result.score,
        delta_e: result.delta_e,
        delta_l: result.delta_l,
        delta_c: result.delta_c,
        delta_h: result.delta_h,
        target_hue_region: result.target_name,
        target_h: result.target.h,
        target_s: result.target.s,
        target_b: result.target.b,
        memorize_duration_ms: _memorizeStartedAt ? (_pickStartedAt || now) - _memorizeStartedAt : null,
        pick_duration_ms: _pickStartedAt ? now - _pickStartedAt : null,
        picker_adjustment_count: _pickerAdjustments,
        picture_choice_index: selectedChoiceIndex != null ? selectedChoiceIndex : null,
        picture_correct_index: correctChoiceIndex != null ? correctChoiceIndex : null,
        call_chosen_name: callChosenName || null,
        call_correct_name: callCorrectName || null,
      });

      // Reset per-round state
      _memorizeStartedAt = null;
      _pickStartedAt = null;
      _pickerAdjustments = 0;
    },

    gameCompleted: function (mode, pickerType, totalScore, roundScores) {
      _inProgress = false;
      capture('game_completed', {
        mode: mode,
        picker_type: (mode === 'picture' || mode === 'call') ? 'none' : pickerType,
        total_score: totalScore,
        round_scores: roundScores,
        total_duration_ms: _gameStartedAt ? Date.now() - _gameStartedAt : null,
        viewport_bucket: viewportBucket(),
      });
    },

    gameAbandoned: function (mode, pickerType, roundsCompleted, currentScreen) {
      if (!_inProgress) return;
      _inProgress = false;
      capture('game_abandoned', {
        mode: mode,
        picker_type: (mode === 'picture' || mode === 'call') ? 'none' : pickerType,
        rounds_completed: roundsCompleted,
        abandoned_at_screen: currentScreen,
        elapsed_ms: _gameStartedAt ? Date.now() - _gameStartedAt : null,
      });
    },

    pickerSwitched: function (fromPicker, toPicker, duringGame) {
      capture('picker_switched', {
        from_picker: fromPicker,
        to_picker: toPicker,
        during_game: duringGame,
      });
    },
  };

  // Fire session_started on load
  window.analytics.sessionStarted();

})();
