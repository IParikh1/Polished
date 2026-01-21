import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { useUpload } from '../../hooks/useUpload'
import clsx from 'clsx'

interface BatchUploadProps {
  batchId: string
}

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'application/rtf': ['.rtf'],
}

export default function BatchUpload({ batchId }: BatchUploadProps) {
  const { isUploading, uploadedCount, totalCount, errors, upload, reset, isLoading } = useUpload(batchId)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        upload(acceptedFiles)
      }
    },
    [upload]
  )

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 100,
    disabled: isLoading,
  })

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={clsx(
          'border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer',
          isDragActive
            ? 'border-primary-400 bg-primary-50'
            : 'border-gray-300 hover:border-gray-400',
          isLoading && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        <Upload
          className={clsx(
            'w-10 h-10 mx-auto mb-4',
            isDragActive ? 'text-primary-500' : 'text-gray-400'
          )}
        />
        {isDragActive ? (
          <p className="text-primary-600 font-medium">Drop the files here...</p>
        ) : (
          <>
            <p className="text-gray-700 font-medium mb-1">
              Drag & drop resume files here
            </p>
            <p className="text-sm text-gray-500">
              or click to browse. Supports PDF, DOCX, DOC, TXT, RTF
            </p>
          </>
        )}
      </div>

      {/* Upload Progress */}
      {isLoading && (
        <div className="p-4 bg-primary-50 rounded-lg">
          <div className="flex items-center gap-3">
            <Loader2 className="w-5 h-5 text-primary-500 animate-spin" />
            <div className="flex-1">
              <div className="flex justify-between text-sm mb-1">
                <span className="font-medium text-primary-700">Uploading...</span>
                <span className="text-primary-600">
                  {uploadedCount}/{totalCount}
                </span>
              </div>
              <div className="h-2 bg-primary-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 transition-all duration-300"
                  style={{
                    width: totalCount > 0 ? `${(uploadedCount / totalCount) * 100}%` : '0%',
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Success Message */}
      {!isLoading && uploadedCount > 0 && errors.length === 0 && (
        <div className="p-4 bg-success-50 rounded-lg flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-success-500" />
          <div className="flex-1">
            <span className="font-medium text-success-700">
              Successfully uploaded {uploadedCount} resume{uploadedCount !== 1 ? 's' : ''}
            </span>
          </div>
          <button onClick={reset} className="text-success-600 hover:text-success-700">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Errors */}
      {errors.length > 0 && (
        <div className="p-4 bg-danger-50 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-danger-500 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium text-danger-700 mb-2">
                {errors.length} file{errors.length !== 1 ? 's' : ''} failed to upload
              </p>
              <ul className="text-sm text-danger-600 space-y-1">
                {errors.slice(0, 5).map((error, i) => (
                  <li key={i}>
                    {error.filename}: {error.error}
                  </li>
                ))}
                {errors.length > 5 && (
                  <li>...and {errors.length - 5} more</li>
                )}
              </ul>
            </div>
            <button onClick={reset} className="text-danger-600 hover:text-danger-700">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Selected Files Preview */}
      {!isLoading && acceptedFiles.length > 0 && uploadedCount === 0 && (
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="font-medium text-gray-700 mb-2">
            Selected {acceptedFiles.length} file{acceptedFiles.length !== 1 ? 's' : ''}:
          </p>
          <ul className="space-y-1 text-sm text-gray-600">
            {acceptedFiles.slice(0, 5).map((file, i) => (
              <li key={i} className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-gray-400" />
                {file.name}
              </li>
            ))}
            {acceptedFiles.length > 5 && (
              <li className="text-gray-400">
                ...and {acceptedFiles.length - 5} more
              </li>
            )}
          </ul>
        </div>
      )}
    </div>
  )
}
