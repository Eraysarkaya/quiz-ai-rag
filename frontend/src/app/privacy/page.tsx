'use client';

import Link from 'next/link';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

export default function PrivacyPage() {
    return (
        <div className="min-h-screen bg-[#131314] text-white">
            {/* Header */}
            <header className="w-full p-6 border-b border-gray-800">
                <div className="max-w-4xl mx-auto flex items-center gap-4">
                    <Link href="/" className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
                        <ArrowLeftIcon className="w-5 h-5" />
                    </Link>
                    <div className="flex items-center gap-2">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold">
                            Q
                        </div>
                        <span className="text-xl font-semibold">Quiz AI</span>
                    </div>
                </div>
            </header>

            {/* Content */}
            <main className="max-w-4xl mx-auto px-6 py-12">
                <h1 className="text-3xl font-bold mb-8">Privacy Policy</h1>
                <p className="text-gray-400 mb-8">Last updated: January 2026</p>

                <div className="space-y-8 text-gray-300">
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">1. Information We Collect</h2>
                        <p className="mb-4">We collect the following types of information:</p>
                        <ul className="list-disc list-inside space-y-2 text-gray-400">
                            <li><strong className="text-gray-300">Account Information:</strong> Email address, name, and profile picture (if using Google Sign-In)</li>
                            <li><strong className="text-gray-300">Quiz Data:</strong> Topics you study, quiz results, and learning progress</li>
                            <li><strong className="text-gray-300">Usage Data:</strong> How you interact with the service to improve your experience</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">2. How We Use Your Information</h2>
                        <p className="mb-4">Your information is used to:</p>
                        <ul className="list-disc list-inside space-y-2 text-gray-400">
                            <li>Provide and maintain the Quiz AI service</li>
                            <li>Save your quiz history and learning progress</li>
                            <li>Personalize your experience with default preferences</li>
                            <li>Improve our AI question generation</li>
                            <li>Communicate important service updates</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">3. Third-Party Services</h2>
                        <p className="mb-4">We use the following third-party services:</p>
                        <ul className="list-disc list-inside space-y-2 text-gray-400">
                            <li><strong className="text-gray-300">Google Sign-In:</strong> For authentication (subject to Google&apos;s Privacy Policy)</li>
                            <li><strong className="text-gray-300">AI Services:</strong> To generate quiz questions (your topics are processed by AI models)</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">4. Data Storage and Security</h2>
                        <p>
                            Your data is stored securely and we implement appropriate technical measures to
                            protect your information. However, no method of transmission over the internet
                            is 100% secure.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">5. Your Rights</h2>
                        <p className="mb-4">You have the right to:</p>
                        <ul className="list-disc list-inside space-y-2 text-gray-400">
                            <li><strong className="text-gray-300">Access:</strong> View your account information and quiz history</li>
                            <li><strong className="text-gray-300">Delete:</strong> Remove your account and all associated data through Settings</li>
                            <li><strong className="text-gray-300">Clear History:</strong> Delete your quiz history while keeping your account</li>
                            <li><strong className="text-gray-300">Update:</strong> Modify your profile information at any time</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">6. Cookies</h2>
                        <p>
                            We use essential cookies and local storage to maintain your session and
                            preferences. These are necessary for the service to function properly.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">7. Children&apos;s Privacy</h2>
                        <p>
                            Quiz AI is intended for users of all ages for educational purposes.
                            We do not knowingly collect personal information from children under 13
                            without parental consent.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">8. Changes to This Policy</h2>
                        <p>
                            We may update this Privacy Policy from time to time. We will notify users
                            of significant changes through the service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">9. Contact</h2>
                        <p>
                            For questions about this Privacy Policy or your data, please contact us
                            through the application.
                        </p>
                    </section>
                </div>

                {/* Footer */}
                <div className="mt-16 pt-8 border-t border-gray-800 text-center text-gray-500 text-sm">
                    <p>© 2025 Quiz AI · <Link href="/terms" className="hover:text-white">Terms of Service</Link></p>
                </div>
            </main>
        </div>
    );
}
