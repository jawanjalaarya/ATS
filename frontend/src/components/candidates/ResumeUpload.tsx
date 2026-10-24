import * as React from "react"
import { Upload, FileText, X, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import apiClient from "@/lib/api"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"

// Candidate response from the upload/parse endpoint
export interface CandidateResponse {
  id: number
  name: string
  email: string
  phone?: string
  location?: string
  skills: string[]
  status: "complete" | "pending_review" | "failed"
  created_at: string
}

type FileStatus = "pending" | "uploading" | "parsing" | "complete" | "failed"

interface UploadFile {
  id: string
  file: File
  progress: number
  status: FileStatus
  error?: string
  candidate?: CandidateResponse
}

interface ResumeUploadProps {
  jobId?: number
  onUploadComplete?: (candidates: CandidateResponse[]) => void
}

const ACCEPTED_EXTENSIONS = [".pdf", ".docx"]
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10 MB

function getFileExtension(filename: string): string {
  const dot = filename.lastIndexOf(".")
  return dot >= 0 ? filename.slice(dot).toLowerCase() : ""
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

const statusBadgeMap: Record<
  FileStatus,
  { variant: "muted" | "warning" | "success" | "destructive"; label: string }
> = {
  pending: { variant: "muted", label: "Pending" },
  uploading: { variant: "muted", label: "Uploading" },
  parsing: { variant: "warning", label: "Parsing" },
  complete: { variant: "success", label: "Complete" },
  failed: { variant: "destructive", label: "Failed" },
}

export function ResumeUpload({ jobId, onUploadComplete }: ResumeUploadProps) {
  const [open, setOpen] = React.useState(false)
  const [uploadFiles, setUploadFiles] = React.useState<UploadFile[]>([])
  const [isDragOver, setIsDragOver] = React.useState(false)
  const [isInvalidDrag, setIsInvalidDrag] = React.useState(false)
  const [announcement, setAnnouncement] = React.useState("")
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const abortControllers = React.useRef<Map<string, AbortController>>(new Map())

  const allDone = uploadFiles.length > 0 && uploadFiles.every(
    (f) => f.status === "complete" || f.status === "failed"
  )

  function validateFile(file: File): string | null {
    const ext = getFileExtension(file.name)
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return "Only PDF and DOCX files are accepted."
    }
    if (file.size > MAX_FILE_SIZE) {
      return "File exceeds 10 MB limit. Please use a smaller file."
    }
    return null
  }

  function addFiles(files: FileList | File[]) {
    const newFiles: UploadFile[] = []
    const errors: string[] = []

    for (const file of Array.from(files)) {
      const error = validateFile(file)
      if (error) {
        errors.push(`${file.name}: ${error}`)
        continue
      }
      newFiles.push({
        id: crypto.randomUUID(),
        file,
        progress: 0,
        status: "pending",
      })
    }

    if (errors.length > 0) {
      errors.forEach((err) => toast.error(err))
      setIsInvalidDrag(true)
      setTimeout(() => setIsInvalidDrag(false), 500)
    }

    if (newFiles.length > 0) {
      setUploadFiles((prev) => [...prev, ...newFiles])
    }
  }

  async function uploadFile(uploadFile: UploadFile) {
    const controller = new AbortController()
    abortControllers.current.set(uploadFile.id, controller)

    // Set uploading
    setUploadFiles((prev) =>
      prev.map((f) =>
        f.id === uploadFile.id ? { ...f, status: "uploading" as const, progress: 0 } : f
      )
    )

    try {
      const formData = new FormData()
      formData.append("file", uploadFile.file)
      if (jobId) {
        formData.append("job_id", jobId.toString())
      }

      const response = await apiClient.post<CandidateResponse>(
        "/candidates/upload",
        formData,
        {
          headers: { "Content-Type": undefined as unknown as string },
          signal: controller.signal,
          onUploadProgress: (progressEvent) => {
            const percent = progressEvent.total
              ? Math.round((progressEvent.loaded / progressEvent.total) * 100)
              : 0
            setUploadFiles((prev) =>
              prev.map((f) =>
                f.id === uploadFile.id ? { ...f, progress: percent } : f
              )
            )
          },
        }
      )

      // Set parsing briefly then complete
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id ? { ...f, status: "parsing" as const, progress: 100 } : f
        )
      )

      // Brief parsing state for UX
      await new Promise((resolve) => setTimeout(resolve, 400))

      const candidate = response.data
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: "complete" as const, candidate }
            : f
        )
      )

      if (candidate.status === "pending_review") {
        toast("Resume uploaded — some fields need manual review.")
      } else {
        toast.success("Resume parsed successfully. Candidate profile created.")
      }
      setAnnouncement(`${uploadFile.file.name} uploaded successfully.`)
    } catch (err) {
      if (controller.signal.aborted) return

      const message =
        err instanceof Error ? err.message : "Upload failed — please check your connection and try again."
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === uploadFile.id
            ? { ...f, status: "failed" as const, error: message }
            : f
        )
      )
      toast.error(message)
      setAnnouncement(`${uploadFile.file.name} upload failed.`)
    } finally {
      abortControllers.current.delete(uploadFile.id)
    }
  }

  async function uploadAll() {
    const pending = uploadFiles.filter((f) => f.status === "pending")
    for (const file of pending) {
      await uploadFile(file)
    }
  }

  function retryFile(fileId: string) {
    const file = uploadFiles.find((f) => f.id === fileId)
    if (file) {
      setUploadFiles((prev) =>
        prev.map((f) =>
          f.id === fileId ? { ...f, status: "pending" as const, progress: 0, error: undefined } : f
        )
      )
      uploadFile({ ...file, status: "pending", progress: 0, error: undefined })
    }
  }

  function removeFile(fileId: string) {
    const controller = abortControllers.current.get(fileId)
    if (controller) {
      controller.abort()
      abortControllers.current.delete(fileId)
    }
    setUploadFiles((prev) => prev.filter((f) => f.id !== fileId))
  }

  function handleDone() {
    const successCandidates = uploadFiles
      .filter((f) => f.status === "complete" && f.candidate)
      .map((f) => f.candidate!)
    onUploadComplete?.(successCandidates)
    setOpen(false)
    setUploadFiles([])
    setAnnouncement("")
  }

  function handleCancel() {
    // Abort all in-progress uploads
    abortControllers.current.forEach((controller) => controller.abort())
    abortControllers.current.clear()
    setOpen(false)
    setUploadFiles([])
    setAnnouncement("")
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    setIsInvalidDrag(false)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files)
    }
  }

  function handleFileInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files)
      e.target.value = ""
    }
  }

  function handleDropzoneClick() {
    fileInputRef.current?.click()
  }

  function handleDropzoneKeyDown(e: React.KeyboardEvent) {
    if (e.key === " " || e.key === "Enter") {
      e.preventDefault()
      fileInputRef.current?.click()
    }
  }

  const hasPending = uploadFiles.some((f) => f.status === "pending")

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Upload data-icon="inline-start" />
          Upload Resumes
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Upload Resumes</DialogTitle>
          <DialogDescription>
            Upload one or more PDF or DOCX files to create candidate profiles.
          </DialogDescription>
        </DialogHeader>

        {/* Dropzone */}
        <div
          role="button"
          tabIndex={0}
          aria-label="Upload resume files"
          onClick={handleDropzoneClick}
          onKeyDown={handleDropzoneKeyDown}
          onDragOver={handleDragOver}
          onDragEnter={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-lg min-h-[160px] p-12 flex flex-col items-center justify-center gap-3 transition-colors duration-[180ms] ease-out cursor-pointer",
            isDragOver && !isInvalidDrag && "border-primary bg-[oklch(0.96_0.02_255)]",
            isInvalidDrag && "border-destructive animate-[shake_150ms_ease-in-out]",
            !isDragOver && !isInvalidDrag && "border-border bg-card"
          )}
        >
          <Upload
            className={cn(
              "size-8",
              isDragOver ? "text-primary" : "text-muted-foreground"
            )}
          />
          <p className="text-sm font-medium text-center">
            Drop resumes here or click to browse
          </p>
          <p className="text-xs text-muted-foreground text-center">
            PDF or DOCX, up to 10 MB each
          </p>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx"
          multiple
          className="hidden"
          onChange={handleFileInputChange}
          aria-hidden="true"
          tabIndex={-1}
        />

        {/* File list */}
        {uploadFiles.length > 0 && (
          <div className="flex flex-col gap-1 max-h-[240px] overflow-y-auto">
            {uploadFiles.map((uf) => {
              const { variant, label } = statusBadgeMap[uf.status]
              return (
                <div
                  key={uf.id}
                  className="flex items-center gap-3 h-[52px] px-2 rounded-md group hover:bg-muted/50"
                >
                  {/* Icon */}
                  {uf.status === "complete" ? (
                    <CheckCircle2 className="size-4 shrink-0 text-[oklch(0.39_0.09_157)]" />
                  ) : uf.status === "failed" ? (
                    <AlertCircle className="size-4 shrink-0 text-destructive" />
                  ) : (
                    <FileText className="size-4 shrink-0 text-muted-foreground" />
                  )}

                  {/* File info + progress */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm truncate">{uf.file.name}</span>
                      <span className="text-xs text-muted-foreground shrink-0">
                        {formatFileSize(uf.file.size)}
                      </span>
                    </div>
                    {(uf.status === "uploading" || uf.status === "parsing") && (
                      <Progress
                        value={uf.progress}
                        className="mt-1 h-1"
                        aria-label={`${uf.file.name} upload progress`}
                      />
                    )}
                  </div>

                  {/* Badge */}
                  <Badge variant={variant} className="shrink-0">
                    {label}
                  </Badge>

                  {/* Retry button for failed */}
                  {uf.status === "failed" && (
                    <button
                      type="button"
                      onClick={() => retryFile(uf.id)}
                      className="p-1 rounded text-muted-foreground hover:text-foreground"
                      aria-label={`Retry upload for ${uf.file.name}`}
                    >
                      <RefreshCw className="size-3.5" />
                    </button>
                  )}

                  {/* Remove button */}
                  <button
                    type="button"
                    onClick={() => removeFile(uf.id)}
                    className="p-1 rounded text-muted-foreground hover:text-foreground opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label={`Remove ${uf.file.name}`}
                  >
                    <X className="size-3.5" />
                  </button>
                </div>
              )
            })}
          </div>
        )}

        {/* Screen reader announcements */}
        <div aria-live="polite" aria-atomic="true" className="sr-only">
          {announcement}
        </div>

        {/* Footer */}
        <DialogFooter>
          {hasPending && (
            <Button onClick={uploadAll}>Upload All</Button>
          )}
          <Button
            variant="default"
            disabled={!allDone}
            onClick={handleDone}
          >
            Done
          </Button>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
