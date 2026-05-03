<script>
    import { toast } from '$lib/stores/toast.js';
    import { fly, fade } from 'svelte/transition';
    import { flip } from 'svelte/animate';
    import { 
        CheckCircleOutline, 
        ExclamationCircleOutline, 
        InfoCircleOutline,
        CloseOutline
    } from 'flowbite-svelte-icons';

    const icons = {
        success: CheckCircleOutline,
        error: ExclamationCircleOutline,
        info: InfoCircleOutline,
        warning: ExclamationCircleOutline
    };

    const colors = {
        success: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20 shadow-emerald-500/10',
        error: 'bg-rose-500/10 text-rose-500 border-rose-500/20 shadow-rose-500/10',
        info: 'bg-blue-500/10 text-blue-500 border-blue-500/20 shadow-blue-500/10',
        warning: 'bg-amber-500/10 text-amber-500 border-amber-500/20 shadow-amber-500/10'
    };
</script>

<div class="fixed top-6 right-6 z-[9999] flex flex-col gap-3 pointer-events-none w-full max-w-sm">
    {#each $toast as t (t.id)}
        <div 
            animate:flip={{ duration: 300 }}
            in:fly={{ x: 100, duration: 400, opacity: 0 }}
            out:fade={{ duration: 200 }}
            class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl border backdrop-blur-xl shadow-2xl {colors[t.type]} group"
        >
            <div class="shrink-0">
                <svelte:component this={icons[t.type]} size="md" />
            </div>
            
            <p class="flex-1 text-sm font-black tracking-tight leading-tight uppercase">
                {t.message}
            </p>

            <button 
                onclick={() => toast.dismiss(t.id)}
                class="shrink-0 p-1 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                aria-label="Dismiss"
            >
                <CloseOutline size="xs" />
            </button>
        </div>
    {/each}
</div>
