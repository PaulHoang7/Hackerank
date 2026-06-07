"use client"

import { useState } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { Send } from "lucide-react"
import { useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { EvidenceCard } from "@/components/questions/evidence-card"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { useAskQuestion, useQuestions } from "@/features/questions/queries"
import type { QuestionResponse } from "@/lib/api/types"
import type { DisplayLanguage } from "@/lib/display-language"

const questionSchema = z.object({
  question: z.string().trim().min(1, "Nhập câu hỏi").max(2000, "Câu hỏi tối đa 2000 ký tự"),
})

type QuestionForm = z.infer<typeof questionSchema>

export { questionSchema }

interface QAChatProps {
  videoId: string
  language?: DisplayLanguage
  demoQuestions?: QuestionResponse[]
  sampleQuestions?: string[]
  onDemoAsk?: (question: string) => QuestionResponse
}

export function QAChat({ videoId, language = "vi", demoQuestions, sampleQuestions, onDemoAsk }: QAChatProps) {
  if (demoQuestions && onDemoAsk) {
    return (
      <DemoQAChat
        questions={demoQuestions}
        sampleQuestions={sampleQuestions ?? []}
        onAsk={onDemoAsk}
        language={language}
      />
    )
  }

  return <LiveQAChat videoId={videoId} language={language} />
}

function LiveQAChat({ videoId, language }: { videoId: string; language: DisplayLanguage }) {
  const questionsQuery = useQuestions(videoId)
  const askMutation = useAskQuestion(videoId)
  const form = useForm<QuestionForm>({
    resolver: zodResolver(questionSchema),
    defaultValues: { question: "" },
  })

  const onSubmit = form.handleSubmit((values) => {
    askMutation.mutate(values.question, {
      onSuccess: () => {
        form.reset()
        toast.success("Đã nhận câu trả lời")
      },
      onError: (error) => toast.error(error.message),
    })
  })

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Q&A evidence</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={onSubmit} className="space-y-2">
          <Textarea placeholder="Ví dụ: Người dẫn giới thiệu giá sản phẩm A lúc nào?" {...form.register("question")} />
          {form.formState.errors.question ? (
            <p className="text-xs text-destructive">{form.formState.errors.question.message}</p>
          ) : null}
          <Button type="submit" disabled={askMutation.isPending}>
            <Send className="h-4 w-4" />
            {askMutation.isPending ? "Đang hỏi..." : "Ask"}
          </Button>
        </form>
        <QuestionThread questions={questionsQuery.data ?? []} language={language} />
      </CardContent>
    </Card>
  )
}

function DemoQAChat({
  questions: initialQuestions,
  sampleQuestions,
  onAsk,
  language,
}: {
  questions: QuestionResponse[]
  sampleQuestions: string[]
  onAsk: (question: string) => QuestionResponse
  language: DisplayLanguage
}) {
  const [question, setQuestion] = useState("")
  const [questions, setQuestions] = useState(initialQuestions)

  const ask = (nextQuestion: string) => {
    const trimmed = nextQuestion.trim()
    if (!trimmed) return
    setQuestions((current) => [{ ...onAsk(trimmed), id: `demo-question-${Date.now()}` }, ...current])
    setQuestion("")
    toast.success("Demo answer generated")
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Q&A evidence</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          className="space-y-2"
          onSubmit={(event) => {
            event.preventDefault()
            ask(question)
          }}
        >
          <Textarea
            placeholder="Ví dụ: Người dẫn giới thiệu giá sản phẩm A lúc nào?"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
          <Button type="submit">
            <Send className="h-4 w-4" />
            Ask demo
          </Button>
        </form>
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase text-muted-foreground">Sample questions</p>
          <div className="flex flex-wrap gap-2">
            {sampleQuestions.slice(0, 6).map((sample) => (
              <button
                key={sample}
                type="button"
                className="rounded-full border bg-background px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                onClick={() => ask(sample)}
              >
                {sample}
              </button>
            ))}
          </div>
        </div>
        <QuestionThread questions={questions} language={language} />
      </CardContent>
    </Card>
  )
}

function QuestionThread({ questions, language }: { questions: QuestionResponse[]; language: DisplayLanguage }) {
  return (
    <div className="max-h-[620px] space-y-3 overflow-y-auto pr-1">
      {questions.map((item) => (
        <div key={item.id} className="rounded-lg border bg-muted/30 p-3">
          <p className="text-sm font-medium">Q: {item.question}</p>
          {item.evidence.length ? (
            <>
              <p className="mt-2 text-sm">A: {item.answer}</p>
              <p className="mt-1 text-xs text-muted-foreground">
                {item.latency_ms} ms · ${item.estimated_cost.toFixed(5)}
              </p>
              <div className="mt-3 space-y-2">
                {item.evidence.map((evidence) => (
                  <EvidenceCard key={`${item.id}-${evidence.timestamp}`} evidence={evidence} language={language} />
                ))}
              </div>
            </>
          ) : (
            <div className="mt-2 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              Backend trả answer không có evidence. FE không hiển thị answer để tránh demo dẫn chứng sai.
            </div>
          )}
        </div>
      ))}
      {!questions.length ? (
        <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
          Chưa có câu hỏi nào cho video này.
        </p>
      ) : null}
    </div>
  )
}
