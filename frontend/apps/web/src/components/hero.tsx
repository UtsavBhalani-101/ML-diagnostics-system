"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { MoveRight, Play } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";

function Hero() {
    const [titleNumber, setTitleNumber] = useState(0);
    const titles = useMemo(
        () => ["data quality", "model risk", "pipeline bugs", "drift patterns", "schema issues"],
        []
    );

    useEffect(() => {
        const timeoutId = setTimeout(() => {
            if (titleNumber === titles.length - 1) {
                setTitleNumber(0);
            } else {
                setTitleNumber(titleNumber + 1);
            }
        }, 2000);
        return () => clearTimeout(timeoutId);
    }, [titleNumber, titles]);

    return (
        <div className="w-full">
            <div className="container mx-auto">
                <div className="flex gap-6 py-16 lg:py-24 items-center justify-center flex-col">
                    {/* Status Badge */}
                    <div>
                        <div className="inline-flex items-center gap-3 px-4 py-1.5 rounded-full border border-primary/30 bg-primary/10">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary" />
                            </span>
                            <span className="text-[10px] font-mono font-medium text-primary uppercase tracking-widest">
                                System Operational
                            </span>
                        </div>
                    </div>

                    {/* Main Headline */}
                    <div className="flex gap-3 flex-col">
                        <h1 className="text-4xl md:text-6xl max-w-3xl tracking-tight text-center font-semibold">
                            <span className="text-foreground">Diagnose your</span>
                            <span className="relative flex w-full justify-center overflow-hidden text-center md:pb-3 md:pt-1">
                                &nbsp;
                                {titles.map((title, index) => (
                                    <motion.span
                                        key={index}
                                        className="absolute font-bold text-primary"
                                        initial={{ opacity: 0, y: "-100" }}
                                        transition={{ type: "spring", stiffness: 50 }}
                                        animate={
                                            titleNumber === index
                                                ? {
                                                    y: 0,
                                                    opacity: 1,
                                                }
                                                : {
                                                    y: titleNumber > index ? -150 : 150,
                                                    opacity: 0,
                                                }
                                        }
                                    >
                                        {title}
                                    </motion.span>
                                ))}
                            </span>
                        </h1>

                        <p className="text-base md:text-lg leading-relaxed tracking-tight text-muted-foreground max-w-xl text-center mx-auto">
                            Evaluate data readiness, detect structural issues, and assess
                            modeling risk—before you commit to any ML pipeline.
                        </p>
                    </div>

                    {/* CTA Buttons */}
                    <div className="flex flex-row gap-3 mt-4">
                        <Link href="/docs">
                            <Button size="lg" variant="outline" className="gap-2 h-11 px-6">
                                Documentation <MoveRight className="w-4 h-4" />
                            </Button>
                        </Link>
                        <Link href="/diagnostics">
                            <Button size="lg" className="gap-2 h-11 px-6">
                                <Play className="w-4 h-4" /> Run Diagnostics
                            </Button>
                        </Link>
                    </div>

                    {/* Bottom Status */}
                    <div className="flex flex-row gap-6 mt-6 opacity-50">
                        <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                            Environment: Production
                        </span>
                        <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                            Status: Awaiting Input
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export { Hero };
