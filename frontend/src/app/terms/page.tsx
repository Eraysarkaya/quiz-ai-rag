'use client';

import Link from 'next/link';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';

export default function TermsPage() {
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
                <h1 className="text-3xl font-bold mb-8">Terms of Service</h1>
                <p className="text-gray-400 mb-8">Last updated: January 2026</p>

                <div className="space-y-8 text-gray-300">
                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">1. Acceptance of Terms</h2>
                        <p>
                            By accessing or using Quiz AI, you agree to be bound by these Terms of Service.
                            If you do not agree to these terms, please do not use our service.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">2. Description of Service</h2>
                        <p>
                            Quiz AI is an AI-powered educational platform that generates science quiz questions
                            using artificial intelligence and retrieval-augmented generation (RAG) technology.
                            The service is provided for educational and learning purposes only.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">3. AI-Generated Content Disclaimer</h2>
                        <p className="mb-4">
                            The quiz questions and explanations provided by Quiz AI are generated using artificial
                            intelligence. While we strive for accuracy, we cannot guarantee that all content is
                            error-free or completely accurate.
                        </p>
                        <ul className="list-disc list-inside space-y-2 text-gray-400">
                            <li>AI-generated content may contain errors or inaccuracies</li>
                            <li>Content should not be used as the sole source for academic or professional decisions</li>
                            <li>Users should verify information with authoritative sources when needed</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">4. User Accounts</h2>
                        <p className="mb-4">
                            To access certain features, you may create an account using email/password or Google Sign-In.
                        </p>
                        <ul className="list-disc list-inside space-y-2 text-gray-400">
                            <li>You are responsible for maintaining the security of your account</li>
                            <li>You must provide accurate information when creating an account</li>
                            <li>You may delete your account and data at any time through Settings</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">5. Acceptable Use</h2>
                        <p className="mb-4">You agree not to:</p>
                        <ul className="list-disc list-inside space-y-2 text-gray-400">
                            <li>Use the service for any unlawful purpose</li>
                            <li>Attempt to bypass security measures or access systems without authorization</li>
                            <li>Use automated systems to access the service in a manner that exceeds reasonable use</li>
                            <li>Share account credentials with others</li>
                        </ul>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">6. Intellectual Property</h2>
                        <p>
                            The Quiz AI service, including its design, features, and underlying technology,
                            is protected by intellectual property rights. Quiz questions generated for you
                            are provided for your personal educational use.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">7. Limitation of Liability</h2>
                        <p>
                            Quiz AI is provided &quot;as is&quot; without warranties of any kind. We are not liable for
                            any damages arising from your use of the service, including but not limited to
                            direct, indirect, incidental, or consequential damages.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">8. Changes to Terms</h2>
                        <p>
                            We may update these Terms of Service from time to time. Continued use of the
                            service after changes constitutes acceptance of the new terms.
                        </p>
                    </section>

                    <section>
                        <h2 className="text-xl font-semibold text-white mb-4">9. Contact</h2>
                        <p>
                            For questions about these Terms of Service, please contact us through the
                            application or visit our website.
                        </p>
                    </section>
                </div>

                {/* Footer */}
                <div className="mt-16 pt-8 border-t border-gray-800 text-center text-gray-500 text-sm">
                    <p>© 2025 Quiz AI · <Link href="/privacy" className="hover:text-white">Privacy Policy</Link></p>
                </div>
            </main>
        </div>
    );
}
