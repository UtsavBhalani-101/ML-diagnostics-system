"use client";

import { useEffect, useRef } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { Route } from "next";

export interface AnimatedTabsProps {
    tabs: { label: string; href: string }[];
}

export function AnimatedTabs({ tabs }: AnimatedTabsProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const activeTabRef = useRef<HTMLButtonElement>(null);
    const router = useRouter();
    const pathname = usePathname();

    const isActivePath = (href: string) =>
        pathname === href || pathname.startsWith(`${href}/`);

    const activeTab = tabs.find((tab) => isActivePath(tab.href))?.label ?? null;

    useEffect(() => {
        const container = containerRef.current;

        if (container && activeTab) {
            const activeTabElement = activeTabRef.current;

            if (activeTabElement) {
                const { offsetLeft, offsetWidth } = activeTabElement;

                const clipLeft = offsetLeft + 16;
                const clipRight = offsetLeft + offsetWidth + 16;

                container.style.clipPath = `inset(0 ${Number(
                    100 - (clipRight / container.offsetWidth) * 100
                ).toFixed()}% 0 ${Number(
                    (clipLeft / container.offsetWidth) * 100
                ).toFixed()}% round 17px)`;
            }
        } else if (container) {
            container.style.clipPath = "inset(0 100% 0 0% round 17px)";
        }
    }, [activeTab, pathname]);

    const handleTabClick = (href: string) => {
        router.push(href as Route);
    };

    return (
        <div className="relative mx-auto flex w-fit flex-col items-center rounded-full border border-primary/10 bg-secondary/50 px-4 py-2">
            <div
                ref={containerRef}
                className="absolute z-10 w-full overflow-hidden [clip-path:inset(0px_100%_0px_0%_round_17px)] [transition:clip-path_0.25s_ease]"
            >
                <div className="relative flex w-full justify-center bg-primary">
                    {tabs.map((tab) => (
                        <button
                            key={tab.href}
                            onClick={() => handleTabClick(tab.href)}
                            className="flex h-8 items-center rounded-full p-3 text-sm font-medium text-primary-foreground"
                            tabIndex={-1}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>
            </div>

            <div className="relative flex w-full justify-center">
                {tabs.map(({ label, href }) => {
                    const isActive = activeTab === label;

                    return (
                        <button
                            key={href}
                            ref={isActive ? activeTabRef : null}
                            onClick={() => handleTabClick(href)}
                            className="flex h-8 cursor-pointer items-center rounded-full p-3 text-sm font-medium text-muted-foreground"
                        >
                            {label}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
