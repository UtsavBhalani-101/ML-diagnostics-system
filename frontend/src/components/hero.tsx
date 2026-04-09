"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { MoveRight, Play } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/status-badge";

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
                <div className="flex flex-col items-center justify-center gap-6 py-16 lg:py-24">
                    <StatusBadge status="info" message="System Operational" />

                    <div className="flex flex-col gap-3">
                        <h1 className="max-w-3xl text-center text-4xl font-semibold tracking-tight md:text-6xl">
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
                                                ? { y: 0, opacity: 1 }
                                                : { y: titleNumber > index ? -150 : 150, opacity: 0 }
                                        }
                                    >
                                        {title}
                                    </motion.span>
                                ))}
                            </span>
                        </h1>

                        <p className="mx-auto max-w-xl text-center text-base leading-relaxed tracking-tight text-muted-foreground md:text-lg">
                            Evaluate data readiness, detect structural issues, and assess
                            modeling risk before you commit to any ML pipeline.
                        </p>
                    </div>

                    <div className="mt-4 flex flex-row gap-3">
                        <Link href="/docs">
                            <Button size="lg" variant="outline" className="h-11 gap-2 px-6">
                                Documentation <MoveRight className="h-4 w-4" />
                            </Button>
                        </Link>
                        <Link href="/diagnostics">
                            <Button size="lg" className="h-11 gap-2 px-6">
                                <Play className="h-4 w-4" /> Run Diagnostics
                            </Button>
                        </Link>
                    </div>

                    <div className="mt-6 flex flex-row gap-6 opacity-50">
                        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                            Environment: Production
                        </span>
                        <span className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                            Status: Awaiting Input
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export { Hero };
