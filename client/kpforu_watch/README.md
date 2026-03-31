# KpForU Watch Client (Flutter)

This app is the lightweight companion of KpForU, focused on focus-timer execution, review confirmation, and quick voice capture.

## Run
1. `cd client/kpforu_watch`
2. `flutter pub get`
3. `flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1`

## Main Features
- TimeFlow focus timer with stage transitions and loop modes
- Initial state shows a single Start button; after start, Pause/Resume + Next stage buttons are shown
- Pause does not trigger save confirmation; save confirmation appears only at session end
- Focus session upload to backend after confirmation
- Review center: due cards + done/snooze actions
- Voice draft upload for AI-generated card drafts
- Watch wallpaper sync support (`/v1/watch/wallpaper`)

## Round-Screen Adaptation
- Safe insets are applied based on the shortest side (~8%)
- Focus confirmation dialog is centered with raised action buttons for better reachability on round watches
- Review/history layouts were adjusted to avoid clipped edge interactions

## Desktop Preview (Windows)
- Preview window is fixed to a square size (`360x360`) to simulate watch viewport consistently
- If window settings change, restart `flutter run` (hot reload is not enough)

## API Integration
- Auth/Binding: `/v1/devices/watch/register`, `/v1/binding/pair`, `/v1/auth/token`
- Focus: `/v1/focus/sessions`
- TimeFlow templates: `/v1/timeflows/templates`
- Reviews: `/v1/reviews/due`, `/v1/reviews/events`, `/v1/watch/review/metrics`
- Voice drafts: `/v1/voice/drafts`, `/v1/voice/drafts/{draft_id}`
- Watch wallpaper: `/v1/watch/wallpaper`

## AI Wait Policy
- Voice upload now waits for backend processing callback via polling (`/v1/voice/drafts/{draft_id}`) instead of returning success right after upload.
- Centralized tuning file: `lib/src/core/ai_wait_policy.dart`
	- `requestTimeout` (default 60s)
	- `pollInterval` (default 2s)
	- `pollTimeout` (default 90s)
	- `pollRequestTimeout` (default 15s)

## Notes
- For Chinese documentation, see `README.zh-CN.md`.
- Set `BASE_URL` to your backend environment before testing.
