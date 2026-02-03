"use client";

export default function DocsPage() {
    return (
        <main className="flex-grow flex flex-col relative min-h-screen">
            {/* Grid Pattern Background */}
            <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0" />

            <section className="relative z-10 flex flex-col items-center justify-center flex-grow py-32 px-6">
                <div className="max-w-4xl w-full text-center">
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-8 text-white">
                        Documentation
                    </h1>
                    <p className="text-lg text-slate-400 font-mono mb-8">
                        Learn how to use the ML Diagnostic System.
                    </p>
                    <div className="border border-white/10 rounded-lg p-8 bg-surface/50 backdrop-blur-sm">
                        <p className="text-slate-500 font-mono text-sm">
                            Documentation coming soon...
                        </p>
                    </div>
                </div>
            </section>
        </main>
    );
}
