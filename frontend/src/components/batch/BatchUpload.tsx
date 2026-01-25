import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2, Settings2 } from 'lucide-react'
import { useUpload } from '../../hooks/useUpload'
import { SalesRoleSelector, SalesRoleDropdown, type SalesRole } from './SalesRoleSelector'
import type { FileWithRole } from '../../api/batchClient'
import clsx from 'clsx'

interface BatchUploadProps {
  batchId: string
  showRoleSelector?: boolean
}

interface PendingFile {
  file: File
  targetRole: SalesRole | null
}

const ACCEPTED_TYPES = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'text/plain': ['.txt'],
  'application/rtf': ['.rtf'],
}

export default function BatchUpload({ batchId, showRoleSelector = true }: BatchUploadProps) {
  const { uploadedCount, totalCount, errors, upload, uploadWithRoles, reset, isLoading } = useUpload(batchId)
  const [defaultRole, setDefaultRole] = useState<SalesRole | null>(null)
  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([])
  const [usePerFileRoles, setUsePerFileRoles] = useState(false)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        if (showRoleSelector) {
          // Store files with default role and wait for user to configure
          const filesWithDefaultRole = acceptedFiles.map((file) => ({
            file,
            targetRole: defaultRole,
          }))
          setPendingFiles(filesWithDefaultRole)
        } else {
          // Upload immediately without role selection
          upload(acceptedFiles)
        }
      }
    },
    [upload, defaultRole, showRoleSelector]
  )

  const handleUpload = useCallback(() => {
    if (pendingFiles.length === 0) return

    if (usePerFileRoles) {
      // Upload with per-file roles
      const filesWithRoles: FileWithRole[] = pendingFiles.map((pf) => ({
        file: pf.file,
        targetRole: pf.targetRole || undefined,
      }))
      uploadWithRoles(filesWithRoles)
    } else {
      // Upload all files with the same default role
      const files = pendingFiles.map((pf) => pf.file)
      upload(files, defaultRole || undefined)
    }
    setPendingFiles([])
  }, [pendingFiles, usePerFileRoles, defaultRole, upload, uploadWithRoles])

  const handleCancelPending = useCallback(() => {
    setPendingFiles([])
    setUsePerFileRoles(false)
  }, [])

  const handleApplyDefaultRoleToAll = useCallback(() => {
    setPendingFiles((prev) =>
      prev.map((pf) => ({
        ...pf,
        targetRole: defaultRole,
      }))
    )
  }, [defaultRole])

  const handleFileRoleChange = useCallback((index: number, role: SalesRole | null) => {
    setPendingFiles((prev) =>
      prev.map((pf, i) => (i === index ? { ...pf, targetRole: role } : pf))
    )
  }, [])

  const handleRemoveFile = useCallback((index: number) => {
    setPendingFiles((prev) => prev.filter((_, i) => i !== index))
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 100,
    disabled: isLoading,
  })

  return (
    <div className="space-y-4">
      {/* Role Selector - Show before upload if enabled */}
      {showRoleSelector && pendingFiles.length === 0 && !isLoading && uploadedCount === 0 && (
        <SalesRoleSelector
          value={defaultRole}
          onChange={setDefaultRole}
          disabled={isLoading}
        />
      )}

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
            {defaultRole && (
              <p className="text-sm text-primary-600 mt-2">
                Default role: <strong>{defaultRole.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</strong>
              </p>
            )}
          </>
        )}
      </div>

      {/* Pending Files - Configure roles before upload */}
      {pendingFiles.length > 0 && !isLoading && (
        <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="flex items-start gap-3">
              <FileText className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-amber-800 mb-1">
                  {pendingFiles.length} file{pendingFiles.length !== 1 ? 's' : ''} ready to upload
                </p>
                <p className="text-sm text-amber-700">
                  {usePerFileRoles
                    ? 'Assign a target role to each resume individually'
                    : 'All resumes will use the same target role'}
                </p>
              </div>
            </div>
            <button
              onClick={() => setUsePerFileRoles(!usePerFileRoles)}
              className={clsx(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                usePerFileRoles
                  ? 'bg-primary-100 text-primary-700'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              )}
            >
              <Settings2 className="w-4 h-4" />
              {usePerFileRoles ? 'Per-file roles ON' : 'Per-file roles'}
            </button>
          </div>

          {!usePerFileRoles ? (
            // Single role for all files
            <div className="mb-4">
              <SalesRoleSelector
                value={defaultRole}
                onChange={setDefaultRole}
                className="mb-2"
              />
            </div>
          ) : (
            // Per-file role selection
            <div className="mb-4 space-y-2 max-h-64 overflow-y-auto">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700">
                  Assign roles to each file:
                </span>
                {defaultRole && (
                  <button
                    onClick={handleApplyDefaultRoleToAll}
                    className="text-xs text-primary-600 hover:text-primary-700"
                  >
                    Apply "{defaultRole.replace(/_/g, ' ')}" to all
                  </button>
                )}
              </div>
              {pendingFiles.map((pf, index) => (
                <div
                  key={`${pf.file.name}-${index}`}
                  className="flex items-center gap-3 p-3 bg-white rounded-md border border-gray-200"
                >
                  <FileText className="w-4 h-4 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate" title={pf.file.name}>
                      {pf.file.name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {(pf.file.size / 1024).toFixed(1)} KB
                    </div>
                  </div>
                  <SalesRoleDropdown
                    value={pf.targetRole}
                    onChange={(role) => handleFileRoleChange(index, role)}
                    className="w-40 flex-shrink-0"
                    placeholder="Select role..."
                  />
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="p-1 text-gray-400 hover:text-danger-600 hover:bg-danger-50 rounded flex-shrink-0"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="flex items-center gap-3">
            <button
              onClick={handleUpload}
              className="btn btn-primary"
            >
              Upload {pendingFiles.length} Resume{pendingFiles.length !== 1 ? 's' : ''}
            </button>
            <button
              onClick={handleCancelPending}
              className="btn btn-secondary"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

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
          <button onClick={() => { reset(); setDefaultRole(null); setUsePerFileRoles(false); }} className="text-success-600 hover:text-success-700">
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
    </div>
  )
}
