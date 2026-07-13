import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva("inline-flex h-10 items-center justify-center gap-2 rounded-[3px] px-4 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 disabled:pointer-events-none disabled:opacity-50", { variants: { variant: {
  default: "bg-navy text-white hover:bg-ink focus-visible:outline-navy",
  outline: "border border-ink/35 bg-transparent text-ink hover:bg-mist focus-visible:outline-accent",
  ghost: "bg-transparent text-ink hover:bg-ink/5 focus-visible:outline-accent",
  risk: "bg-risk text-white hover:bg-[#7d2b27] focus-visible:outline-risk",
} }, defaultVariants: { variant: "default" } });

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> { asChild?: boolean }
export function Button({ className, variant, asChild = false, ...props }: ButtonProps) { const Comp = asChild ? Slot : "button"; return <Comp className={cn(buttonVariants({ variant, className }))} {...props} />; }
