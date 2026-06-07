from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_session
from app.core.exceptions import AppError
from app.models import Question
from app.repositories.videos import get_questions, get_video
from app.schemas.question import QuestionRequest, QuestionResponse
from app.services.qa.service import answer_question, build_question_response, build_question_responses

router = APIRouter(prefix="/videos/{video_id}/questions", tags=["questions"])


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def ask_question(
    video_id: str,
    payload: QuestionRequest,
    session: AsyncSession = Depends(get_session),
) -> QuestionResponse:
    video = await get_video(session, video_id)
    if not video:
        raise AppError("VIDEO_NOT_FOUND", "Video not found", status.HTTP_404_NOT_FOUND)
    return await answer_question(session, video_id, payload.question)


@router.get("", response_model=list[QuestionResponse])
async def list_questions(video_id: str, session: AsyncSession = Depends(get_session)) -> list[QuestionResponse]:
    video = await get_video(session, video_id)
    if not video:
        raise AppError("VIDEO_NOT_FOUND", "Video not found", status.HTTP_404_NOT_FOUND)
    questions = await get_questions(session, video_id)
    return await build_question_responses(session, questions)


@router.get("/{question_id}", response_model=QuestionResponse)
async def question_detail(
    video_id: str,
    question_id: str,
    session: AsyncSession = Depends(get_session),
) -> QuestionResponse:
    question = await session.scalar(select(Question).where(Question.video_id == video_id, Question.id == question_id))
    if not question:
        raise AppError("QUESTION_NOT_FOUND", "Question not found", status.HTTP_404_NOT_FOUND)
    return await build_question_response(session, question)
