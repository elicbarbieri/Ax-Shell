#!/usr/bin/env sh

# Check if animations are disabled (game mode is active)
check_gamemode() {
    HYPRGAMEMODE=$(hyprctl getoption animations:enabled | awk 'NR==1{print $2}')
    if [ "$HYPRGAMEMODE" = 0 ] ; then 
        echo "t"
        return 0
    else
        echo "f"
        return 1
    fi
}

# Toggle game mode state
toggle_gamemode() {
    HYPRGAMEMODE=$(hyprctl getoption animations:enabled | awk 'NR==1{print $2}')
    if [ "$HYPRGAMEMODE" = 1 ] ; then
        # Hyprland 0.55 dropped the legacy `hyprctl keyword` parser ("keyword
        # can't work with non-legacy parsers. Use eval."). Runtime config
        # overrides now go through the Lua API via `hyprctl eval hl.config{...}`.
        hyprctl eval 'hl.config({
            animations = { enabled = false },
            decoration = { shadow = { enabled = false }, blur = { enabled = false }, rounding = 0 },
            general = { gaps_in = 0, gaps_out = 0, border_size = 1 },
        })'
        exit
    fi
    hyprctl reload
}

# Main script logic
case "$1" in
    check)
        check_gamemode
        ;;
    *)
        toggle_gamemode
        ;;
esac
