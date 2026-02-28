# KpForU Watch Client (Flutter)

This app is the lightweight companion of KpForU, focused on focus-timer execution, review confirmation, and quick voice capture.

## Run
1. `cd client/kpforu_watch`
2. `flutter pub get`
3. `flutter run -d windows --dart-define=BASE_URL=http://127.0.0.1:8000/v1`

## Main Features
- TimeFlow focus timer with stage transitions (study/break/long break)
- Focus session upload to backend after completion
- Review center: due cards + done/snooze actions
- Voice draft upload for AI-generated card drafts
- Wallpaper customization support

## API Integration
- Auth/Binding: `/v1/devices/watch/register`, `/v1/binding/pair`, `/v1/auth/token`
- Focus: `/v1/focus/sessions`
- TimeFlow templates: `/v1/timeflows/templates`
- Reviews: `/v1/reviews/due`, `/v1/reviews/events`, `/v1/watch/review/metrics`
- Voice drafts: `/v1/voice/drafts`, `/v1/voice/drafts/{draft_id}`

## Notes
- For Chinese documentation, see `README.zh-CN.md`.
- Set `BASE_URL` to your backend environment before testing.
