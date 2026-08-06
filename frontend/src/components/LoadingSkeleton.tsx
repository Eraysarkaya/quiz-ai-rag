'use client';

/**
 * LoadingSkeleton - Animated skeleton loader for quiz generation
 */

interface LoadingSkeletonProps {
    message?: string;
}

export default function LoadingSkeleton({ message = 'Generating your quiz...' }: LoadingSkeletonProps) {
    return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
            {/* Spinner */}
            <div className="relative mb-6">
                <div className="w-16 h-16 border-4 border-[#3d3d3d] rounded-full animate-spin border-t-[#8AB4F8]" />
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-8 h-8 bg-gradient-to-br from-[#8AB4F8] to-[#7B68EE] rounded-full animate-pulse" />
                </div>
            </div>

            {/* Message */}
            <p className="text-[#9AA0A6] text-lg mb-8">{message}</p>

            {/* Skeleton Cards */}
            <div className="w-full max-w-2xl space-y-4">
                {/* Question skeleton */}
                <div className="bg-[#1E1F20] rounded-2xl p-6 animate-pulse">
                    <div className="h-4 bg-[#3d3d3d] rounded w-1/4 mb-4" />
                    <div className="h-6 bg-[#3d3d3d] rounded w-full mb-2" />
                    <div className="h-6 bg-[#3d3d3d] rounded w-3/4" />
                </div>

                {/* Options skeleton */}
                <div className="space-y-3">
                    {[1, 2, 3, 4].map((i) => (
                        <div
                            key={i}
                            className="bg-[#1E1F20] rounded-xl p-4 animate-pulse"
                            style={{ animationDelay: `${i * 100}ms` }}
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-8 h-8 bg-[#3d3d3d] rounded-full" />
                                <div className="h-5 bg-[#3d3d3d] rounded flex-1" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Progress bar */}
            <div className="w-full max-w-2xl mt-8">
                <div className="h-1 bg-[#3d3d3d] rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-[#8AB4F8] to-[#7B68EE] rounded-full animate-loading-bar" />
                </div>
            </div>
        </div>
    );
}
