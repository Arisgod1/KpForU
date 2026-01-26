from fastapi import APIRouter

from app.api import auth, binding, timeflow, focus, cards, reviews, watch, voice, ai

router = APIRouter()
router.include_router(binding.router)
router.include_router(auth.router)
router.include_router(timeflow.router)
router.include_router(focus.router)
router.include_router(cards.router)
router.include_router(reviews.router)
router.include_router(watch.router)
router.include_router(voice.router)
router.include_router(ai.router)
