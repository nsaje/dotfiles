;; -*- mode: emacs-lisp -*-
;; This file is loaded by Spacemacs at startup.
;; It must be stored in your home directory.

(defun dotspacemacs/layers ()
  "Configuration Layers declaration.
You should not put any user code in this function besides modifying the variable
values."
  (setq-default
   ;; Base distribution to use. This is a layer contained in the directory
   ;; `+distribution'. For now available distributions are `spacemacs-base'
   ;; or `spacemacs'. (default 'spacemacs)
   dotspacemacs-distribution 'spacemacs
   ;; Lazy installation of layers (i.e. layers are installed only when a file
   ;; with a supported type is opened). Possible values are `all', `unused'
   ;; and `nil'. `unused' will lazy install only unused layers (i.e. layers
   ;; not listed in variable `dotspacemacs-configuration-layers'), `all' will
   ;; lazy install any layer that support lazy installation even the layers
   ;; listed in `dotspacemacs-configuration-layers'. `nil' disable the lazy
   ;; installation feature and you have to explicitly list a layer in the
   ;; variable `dotspacemacs-configuration-layers' to install it.
   ;; (default 'unused)
   dotspacemacs-enable-lazy-installation 'unused
   ;; If non-nil then Spacemacs will ask for confirmation before installing
   ;; a layer lazily. (default t)
   dotspacemacs-ask-for-lazy-installation t
   ;; If non-nil layers with lazy install support are lazy installed.
   ;; List of additional paths where to look for configuration layers.
   ;; Paths must have a trailing slash (i.e. `~/.mycontribs/')
   dotspacemacs-configuration-layer-path '()
   ;; List of configuration layers to load.
   dotspacemacs-configuration-layers
   '(
     javascript
     html
     yaml
     rust
     python
     sql
     go
     gtags
     ;; ----------------------------------------------------------------
     ;; Example of useful layers you may want to use right away.
     ;; Uncomment some layer names and press <SPC f e R> (Vim style) or
     ;; <M-m f e R> (Emacs style) to install them.
     ;; ----------------------------------------------------------------
     helm
     auto-completion
     ;; company
     better-defaults
     emacs-lisp
     git
     markdown
     imenu-list
     (org :variables
          org-projectile-file "~/Dropbox/org/TODOs.org")
     (shell :variables
            shell-default-height 20
            shell-default-position 'right)
     (spell-checking :variables
                     spell-checking-enable-by-default nil)
     syntax-checking
     version-control
     ;; notmuch
     ;; mu4e
     )
   ;; List of additional packages that will be installed without being
   ;; wrapped in a layer. If you need some configuration for these
   ;; packages, then consider creating a layer. You can also put the
   ;; configuration in `dotspacemacs/user-config'.
   dotspacemacs-additional-packages '(simpleclip flyspell-lazy)
   ;; A list of packages that cannot be updated.
   dotspacemacs-frozen-packages '()
   ;; A list of packages that will not be installed and loaded.
   dotspacemacs-excluded-packages '()
   ;; Defines the behaviour of Spacemacs when installing packages.
   ;; Possible values are `used-only', `used-but-keep-unused' and `all'.
   ;; `used-only' installs only explicitly used packages and uninstall any
   ;; unused packages as well as their unused dependencies.
   ;; `used-but-keep-unused' installs only the used packages but won't uninstall
   ;; them if they become unused. `all' installs *all* packages supported by
   ;; Spacemacs and never uninstall them. (default is `used-only')
   dotspacemacs-install-packages 'used-only)
 )

(defun dotspacemacs/init ()
  "Initialization function.
This function is called at the very startup of Spacemacs initialization
before layers configuration.
You should not put any user code in there besides modifying the variable
values."
  ;; This setq-default sexp is an exhaustive list of all the supported
  ;; spacemacs settings.
  (setq-default
   ;; If non nil ELPA repositories are contacted via HTTPS whenever it's
   ;; possible. Set it to nil if you have no way to use HTTPS in your
   ;; environment, otherwise it is strongly recommended to let it set to t.
   ;; This variable has no effect if Emacs is launched with the parameter
   ;; `--insecure' which forces the value of this variable to nil.
   ;; (default t)
   dotspacemacs-elpa-https t
   ;; Maximum allowed time in seconds to contact an ELPA repository.
   dotspacemacs-elpa-timeout 5
   ;; If non nil then spacemacs will check for updates at startup
   ;; when the current branch is not `develop'. Note that checking for
   ;; new versions works via git commands, thus it calls GitHub services
   ;; whenever you start Emacs. (default nil)
   dotspacemacs-check-for-update nil
   ;; If non-nil, a form that evaluates to a package directory. For example, to
   ;; use different package directories for different Emacs versions, set this
   ;; to `emacs-version'.
   dotspacemacs-elpa-subdirectory nil
   ;; One of `vim', `emacs' or `hybrid'.
   ;; `hybrid' is like `vim' except that `insert state' is replaced by the
   ;; `hybrid state' with `emacs' key bindings. The value can also be a list
   ;; with `:variables' keyword (similar to layers). Check the editing styles
   ;; section of the documentation for details on available variables.
   ;; (default 'vim)
   dotspacemacs-editing-style 'vim
   ;; If non nil output loading progress in `*Messages*' buffer. (default nil)
   dotspacemacs-verbose-loading nil
   ;; Specify the startup banner. Default value is `official', it displays
   ;; the official spacemacs logo. An integer value is the index of text
   ;; banner, `random' chooses a random text banner in `core/banners'
   ;; directory. A string value must be a path to an image format supported
   ;; by your Emacs build.
   ;; If the value is nil then no banner is displayed. (default 'official)
   dotspacemacs-startup-banner 'official
   ;; List of items to show in startup buffer or an association list of
   ;; the form `(list-type . list-size)`. If nil then it is disabled.
   ;; Possible values for list-type are:
   ;; `recents' `bookmarks' `projects' `agenda' `todos'."
   ;; List sizes may be nil, in which case
   ;; `spacemacs-buffer-startup-lists-length' takes effect.
   dotspacemacs-startup-lists '((recents . 5)
                                (projects . 7))
   ;; True if the home buffer should respond to resize events.
   dotspacemacs-startup-buffer-responsive t
   ;; Default major mode of the scratch buffer (default `text-mode')
   dotspacemacs-scratch-mode 'text-mode
   ;; List of themes, the first of the list is loaded when spacemacs starts.
   ;; Press <SPC> T n to cycle to the next theme in the list (works great
   ;; with 2 themes variants, one dark and one light)
   dotspacemacs-themes '(leuven
                         solarized-light
                         material-light
                         zenburn
                         ;; spacemacs-dark
                         ;; spacemacs-light
                         )
   ;; If non nil the cursor color matches the state color in GUI Emacs.
   dotspacemacs-colorize-cursor-according-to-state nil
   ;; Default font, or prioritized list of fonts. `powerline-scale' allows to
   ;; quickly tweak the mode-line size to make separators look not too crappy.
   dotspacemacs-default-font '("Iosevka Term"
                               :size 18
                               :weight normal
                               :width normal
                               :powerline-scale 1.1)
   ;; The leader key
   dotspacemacs-leader-key "SPC"
   ;; The key used for Emacs commands (M-x) (after pressing on the leader key).
   ;; (default "SPC")
   dotspacemacs-emacs-command-key "SPC"
   ;; The key used for Vim Ex commands (default ":")
   dotspacemacs-ex-command-key ":"
   ;; The leader key accessible in `emacs state' and `insert state'
   ;; (default "M-m")
   dotspacemacs-emacs-leader-key "M-m"
   ;; Major mode leader key is a shortcut key which is the equivalent of
   ;; pressing `<leader> m`. Set it to `nil` to disable it. (default ",")
   dotspacemacs-major-mode-leader-key ","
   ;; Major mode leader key accessible in `emacs state' and `insert state'.
   ;; (default "C-M-m")
   dotspacemacs-major-mode-emacs-leader-key "C-M-m"
   ;; These variables control whether separate commands are bound in the GUI to
   ;; the key pairs C-i, TAB and C-m, RET.
   ;; Setting it to a non-nil value, allows for separate commands under <C-i>
   ;; and TAB or <C-m> and RET.
   ;; In the terminal, these pairs are generally indistinguishable, so this only
   ;; works in the GUI. (default nil)
   dotspacemacs-distinguish-gui-tab t  ;; so C-i works for jump forward
   ;; If non nil `Y' is remapped to `y$' in Evil states. (default nil)
   dotspacemacs-remap-Y-to-y$ nil
   ;; If non-nil, the shift mappings `<' and `>' retain visual state if used
   ;; there. (default t)
   dotspacemacs-retain-visual-state-on-shift t
   ;; If non-nil, J and K move lines up and down when in visual mode.
   ;; (default nil)
   dotspacemacs-visual-line-move-text nil
   ;; If non nil, inverse the meaning of `g' in `:substitute' Evil ex-command.
   ;; (default nil)
   dotspacemacs-ex-substitute-global nil
   ;; Name of the default layout (default "Default")
   dotspacemacs-default-layout-name "Default"
   ;; If non nil the default layout name is displayed in the mode-line.
   ;; (default nil)
   dotspacemacs-display-default-layout nil
   ;; If non nil then the last auto saved layouts are resume automatically upon
   ;; start. (default nil)
   dotspacemacs-auto-resume-layouts t
   ;; Size (in MB) above which spacemacs will prompt to open the large file
   ;; literally to avoid performance issues. Opening a file literally means that
   ;; no major mode or minor modes are active. (default is 1)
   dotspacemacs-large-file-size 1
   ;; Location where to auto-save files. Possible values are `original' to
   ;; auto-save the file in-place, `cache' to auto-save the file to another
   ;; file stored in the cache directory and `nil' to disable auto-saving.
   ;; (default 'cache)
   dotspacemacs-auto-save-file-location 'cache
   ;; Maximum number of rollback slots to keep in the cache. (default 5)
   dotspacemacs-max-rollback-slots 5
   ;; If non nil, `helm' will try to minimize the space it uses. (default nil)
   dotspacemacs-helm-resize nil
   ;; if non nil, the helm header is hidden when there is only one source.
   ;; (default nil)
   dotspacemacs-helm-no-header nil
   ;; define the position to display `helm', options are `bottom', `top',
   ;; `left', or `right'. (default 'bottom)
   dotspacemacs-helm-position 'bottom
   ;; Controls fuzzy matching in helm. If set to `always', force fuzzy matching
   ;; in all non-asynchronous sources. If set to `source', preserve individual
   ;; source settings. Else, disable fuzzy matching in all sources.
   ;; (default 'always)
   dotspacemacs-helm-use-fuzzy 'always
   ;; If non nil the paste micro-state is enabled. When enabled pressing `p`
   ;; several times cycle between the kill ring content. (default nil)
   dotspacemacs-enable-paste-transient-state nil
   ;; Which-key delay in seconds. The which-key buffer is the popup listing
   ;; the commands bound to the current keystroke sequence. (default 0.4)
   dotspacemacs-which-key-delay 0.4
   ;; Which-key frame position. Possible values are `right', `bottom' and
   ;; `right-then-bottom'. right-then-bottom tries to display the frame to the
   ;; right; if there is insufficient space it displays it at the bottom.
   ;; (default 'bottom)
   dotspacemacs-which-key-position 'bottom
   ;; If non nil a progress bar is displayed when spacemacs is loading. This
   ;; may increase the boot time on some systems and emacs builds, set it to
   ;; nil to boost the loading time. (default t)
   dotspacemacs-loading-progress-bar t
   ;; If non nil the frame is fullscreen when Emacs starts up. (default nil)
   ;; (Emacs 24.4+ only)
   dotspacemacs-fullscreen-at-startup nil
   ;; If non nil `spacemacs/toggle-fullscreen' will not use native fullscreen.
   ;; Use to disable fullscreen animations in OSX. (default nil)
   dotspacemacs-fullscreen-use-non-native nil
   ;; If non nil the frame is maximized when Emacs starts up.
   ;; Takes effect only if `dotspacemacs-fullscreen-at-startup' is nil.
   ;; (default nil) (Emacs 24.4+ only)
   dotspacemacs-maximized-at-startup nil
   ;; A value from the range (0..100), in increasing opacity, which describes
   ;; the transparency level of a frame when it's active or selected.
   ;; Transparency can be toggled through `toggle-transparency'. (default 90)
   dotspacemacs-active-transparency 90
   ;; A value from the range (0..100), in increasing opacity, which describes
   ;; the transparency level of a frame when it's inactive or deselected.
   ;; Transparency can be toggled through `toggle-transparency'. (default 90)
   dotspacemacs-inactive-transparency 90
   ;; If non nil show the titles of transient states. (default t)
   dotspacemacs-show-transient-state-title t
   ;; If non nil show the color guide hint for transient state keys. (default t)
   dotspacemacs-show-transient-state-color-guide t
   ;; If non nil unicode symbols are displayed in the mode line. (default t)
   dotspacemacs-mode-line-unicode-symbols t
   ;; If non nil smooth scrolling (native-scrolling) is enabled. Smooth
   ;; scrolling overrides the default behavior of Emacs which recenters point
   ;; when it reaches the top or bottom of the screen. (default t)
   dotspacemacs-smooth-scrolling t
   ;; If non nil line numbers are turned on in all `prog-mode' and `text-mode'
   ;; derivatives. If set to `relative', also turns on relative line numbers.
   ;; (default nil)
   dotspacemacs-line-numbers nil
   ;; Code folding method. Possible values are `evil' and `origami'.
   ;; (default 'evil)
   dotspacemacs-folding-method 'evil
   ;; If non-nil smartparens-strict-mode will be enabled in programming modes.
   ;; (default nil)
   dotspacemacs-smartparens-strict-mode nil
   ;; If non-nil pressing the closing parenthesis `)' key in insert mode passes
   ;; over any automatically added closing parenthesis, bracket, quote, etc…
   ;; This can be temporary disabled by pressing `C-q' before `)'. (default nil)
   dotspacemacs-smart-closing-parenthesis nil
   ;; Select a scope to highlight delimiters. Possible values are `any',
   ;; `current', `all' or `nil'. Default is `all' (highlight any scope and
   ;; emphasis the current one). (default 'all)
   dotspacemacs-highlight-delimiters 'all
   ;; If non nil, advise quit functions to keep server open when quitting.
   ;; (default nil)
   dotspacemacs-persistent-server nil
   ;; List of search tool executable names. Spacemacs uses the first installed
   ;; tool of the list. Supported tools are `ag', `pt', `ack' and `grep'.
   ;; (default '("ag" "pt" "ack" "grep"))
   dotspacemacs-search-tools '("ag" "pt" "ack" "grep")
   ;; The default package repository used if no explicit repository has been
   ;; specified with an installed package.
   ;; Not used for now. (default nil)
   dotspacemacs-default-package-repository nil
   ;; Delete whitespace while saving buffer. Possible values are `all'
   ;; to aggressively delete empty line and long sequences of whitespace,
   ;; `trailing' to delete only the whitespace at end of lines, `changed'to
   ;; delete only whitespace for changed lines or `nil' to disable cleanup.
   ;; (default nil)
   dotspacemacs-whitespace-cleanup nil
   ))

(defun dotspacemacs/user-init ()
  "Initialization function for user code.
It is called immediately after `dotspacemacs/init', before layer configuration
executes.
 This function is mostly useful for variables that need to be set
before packages are loaded. If you are unsure, you should try in setting them in
`dotspacemacs/user-config' first."
    ;; For python
    (add-hook 'python-mode-hook #'(lambda () (modify-syntax-entry ?_ "w")))
    ;; For ruby
    (add-hook 'ruby-mode-hook #'(lambda () (modify-syntax-entry ?_ "w")))
    ;; For Javascript
    (add-hook 'js2-mode-hook #'(lambda () (modify-syntax-entry ?_ "w")))
  )

(defun dotspacemacs/user-config ()
  "Configuration function for user code.
This function is called at the very end of Spacemacs initialization after
layers configuration.
This is the place where most of your configurations should be done. Unless it is
explicitly specified that a variable should be set before a package is loaded,
you should place your code here."
    (global-linum-mode)
    ;; (with-eval-after-load 'org-agenda
    ;;   (require 'org-projectile)
    ;;   (push "~/org/TODOs.org" org-agenda-files))
    (with-eval-after-load 'company
      (define-key company-active-map (kbd "C-w") 'evil-delete-backward-word)
      )
    (with-eval-after-load 'helm
      (define-key helm-map (kbd "C-w") 'evil-delete-backward-word)
      )
    (remove-hook 'prog-mode-hook #'smartparens-mode)
    (spacemacs/toggle-smartparens-globally-off)
    (define-key evil-window-map "q" 'delete-window)

    ; mu4e
    ;;location of my maildir
    ;; (setq mu4e-maildir (expand-file-name "~/mbsync"))
    ;; (setq mu4e-enable-notifications t)

    ;; reply/forward citation
    ;; (setq message-citation-line-format "\n\nOn %a %d %b %Y at %R, %f wrote:\n")
    ;; (setq message-citation-line-function 'message-insert-formatted-citation-line)

    ;; (with-eval-after-load 'mu4e-alert
    ;;   ;; Enable Desktop notifications
    ;;   (mu4e-alert-set-default-style 'notifications)) ; For linux
    ;; (setq mu4e-alert-interesting-mail-query "flag:unread AND maildir:/INBOX"
    ;;       mu4e-enable-mode-line t)
    ;; ;;rename files when moving
    ;; ;;NEEDED FOR MBSYNC
    ;; (setq mu4e-change-filenames-when-moving t)
    ;; (defun my-render-html-message ()
    ;;   (let ((dom (libxml-parse-html-region (point-min) (point-max))))
    ;;     (erase-buffer)
    ;;     (shr-insert-document dom)
    ;;     (goto-char (point-min))))
    ;; (setq mu4e-html2text-command 'my-render-html-message)
    ;; (setq mu4e-get-mail-command "mbsync gmail"
    ;;       mu4e-update-interval 30)
    ;; (setq mu4e-sent-messages-behavior 'delete)
    ;; (setq mu4e-compose-format-flowed t)
    ;; ;; (add-hook 'mu4e-compose-mode-hook
    ;; ;;   (lambda ()
    ;; ;;     (use-hard-newlines t 'guess)))
    ;; (setq mu4e-compose-signature-auto-include nil)
    ;; (setq
    ;;   user-mail-address "nejc.saje@zemanta.com"
    ;;   user-full-name  "Nejc Saje"
    ;;   mu4e-compose-signature nil
    ;;   )
    ;; (setq message-send-mail-function 'smtpmail-send-it
    ;;     smtpmail-stream-type 'starttls
    ;;     smtpmail-default-smtp-server "smtp.gmail.com"
    ;;     smtpmail-smtp-server "smtp.gmail.com"
    ;;     smtpmail-smtp-service 587)
    ;; ;; don't keep message buffers around
    ;; (setq message-kill-buffer-on-exit t)

    (setq-default frame-title-format "Spacemacs - %b (%f)")

  ;;; scroll one line at a time (less "jumpy" than defaults)
    (setq mouse-wheel-scroll-amount '(2 ((shift) . 1))) ;; two lines at a time
    (setq mouse-wheel-progressive-speed nil) ;; don't accelerate scrolling
    (setq mouse-wheel-follow-mouse 't) ;; scroll window under mouse
    (setq scroll-preserve-screen-position 't)
    (setq scroll-margin 5)

    ;; clipboard preferences
    (simpleclip-mode 1)

    ;; ORG MODE CONFIG
    (setq org-agenda-files '("~/Dropbox/org/TODOs.org"))
    (setq org-todo-keywords
          (quote ((sequence "TODO(t)" "NEXT(n)" "|" "DONE(d)")
                  (sequence "WAITING(w@/!)" "HOLD(h@/!)" "|" "CANCELLED(c@/!)" "PHONE" "MEETING"))))

    (setq org-todo-keyword-faces
          (quote (("TODO" :foreground "red" :weight bold)
                  ("NEXT" :foreground "blue" :weight bold)
                  ("DONE" :foreground "forest green" :weight bold)
                  ("WAITING" :foreground "orange" :weight bold)
                  ("HOLD" :foreground "magenta" :weight bold)
                  ("CANCELLED" :foreground "forest green" :weight bold)
                  ("MEETING" :foreground "forest green" :weight bold)
                  ("PHONE" :foreground "forest green" :weight bold))))
    (setq org-directory "~/Dropbox/org")
    (setq org-default-notes-file "~/Dropbox/org/TODOs.org")

    ;; Capture templates for: TODO tasks, Notes, appointments, phone calls, meetings, and org-protocol
    (setq org-capture-templates
          (quote (("t" "todo" entry (file+headline "~/Dropbox/org/TODOs.org" "General")
                  "* TODO %?\n")
                  ;; ("r" "respond" entry (file+headline "~/Dropbox/org/TODOs.org" "General")
                  ;; "* NEXT Respond to %:from on %:subject\nSCHEDULED: %t\n%U\n%a\n" :clock-in t :clock-resume t :immediate-finish t)
                  ;; ("r" "respond" entry (file+headline "~/Dropbox/org/TODOs.org" "General")
                  ;;  "* NEXT Respond to %f on %s\nSCHEDULED: %t\n%U\n%a\n" :clock-in t :clock-resume t :immediate-finish t)
                  ("n" "note" entry (file+headline "~/Dropbox/org/TODOs.org" "Notes")
                  "* %? :NOTE:\n")
                  ("m" "Meeting" entry (file+headline "~/Dropbox/org/TODOs.org" "Meetings")
                  "* MEETING with %? :MEETING:\n%U\n\n"))))
    (setq org-mu4e-link-query-in-headers-mode nil)

    ;; persp keybindings
    (define-key window-numbering-keymap "\M-0" 'spacemacs/persp-switch-to-0)
    (define-key window-numbering-keymap "\M-1" 'spacemacs/persp-switch-to-1)
    (define-key window-numbering-keymap "\M-2" 'spacemacs/persp-switch-to-2)
    (define-key window-numbering-keymap "\M-3" 'spacemacs/persp-switch-to-3)
    (define-key window-numbering-keymap "\M-4" 'spacemacs/persp-switch-to-4)
    (define-key window-numbering-keymap "\M-5" 'spacemacs/persp-switch-to-5)
    (define-key window-numbering-keymap "\M-6" 'spacemacs/persp-switch-to-6)
    (define-key window-numbering-keymap "\M-7" 'spacemacs/persp-switch-to-7)
    (define-key window-numbering-keymap "\M-8" 'spacemacs/persp-switch-to-8)
    (define-key window-numbering-keymap "\M-9" 'spacemacs/persp-switch-to-9)

    ;; display which function we're in
    (which-function-mode)

    ;; find other file
    (with-eval-after-load 'projectile
      (push '("html" "js") projectile-other-file-alist) ;; switch from html -> js
      (push '("js" "html") projectile-other-file-alist) ;; switch from js -> html
      (push '("component.js" "component.html") projectile-other-file-alist) ;; switch from js -> html
      (push '("component.html" "component.js") projectile-other-file-alist) ;; switch from html -> js
     )

    ;; (push "dist" 'projectile-globally-ignored-directories)
    ;; (push "node_modules" 'projectile-globally-ignored-directories)
    (setq projectile-use-git-grep 1)

    ;; lazy spellcheck
    (flyspell-lazy-mode 1)

    ;; Angular imenu
    ;; (setq javascript-common-imenu-regex-list
    ;;       '(("Attribute" " \\([a-z][a-zA-Z0-9-_]+\\) *= *\{[a-zA-Z0-9_.(), ]+\}\\( \\|$\\)" 1)
    ;;         ("Controller" "[. \t]controller([ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("Controller" "[. \t]controllerAs:[ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("Filter" "[. \t]filter([ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("State" "[. \t]state[(:][ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("Factory" "[. \t]factory([ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("Service" "[. \t]service([ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("Module" "[. \t]module( *['\"]\\([a-zA-Z0-9_.]+\\)['\"], *\\[" 1)
    ;;         ("ngRoute" "[. \t]when(\\(['\"][a-zA-Z0-9_\/]+['\"]\\)" 1)
    ;;         ("Directive" "[. \t]directive([ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("Event" "[. \t]\$on([ \t]*['\"]\\([^'\"]+\\)" 1)
    ;;         ("Config" "[. \t]config([ \t]*function *( *\\([^\)]+\\)" 1)
    ;;         ("Config" "[. \t]config([ \t]*\\[ *['\"]\\([^'\"]+\\)" 1)
    ;;         ("OnChange" "[ \t]*\$(['\"]\\([^'\"]*\\)['\"]).*\.change *( *function" 1)
    ;;         ("OnClick" "[ \t]*\$([ \t]*['\"]\\([^'\"]*\\)['\"]).*\.click *( *function" 1)
    ;;         ("Watch" "[. \t]\$watch( *['\"]\\([^'\"]+\\)" 1)
    ;;         ("Function" "function[ \t]+\\([a-zA-Z0-9_$.]+\\)[ \t]*(" 1)
    ;;         ("Function" "^[ \t]*\\([a-zA-Z0-9_$.]+\\)[ \t]*=[ \t]*function[ \t]*(" 1)
    ;;         ;; {{ es6 beginning
    ;;         ("Function" "^[ \t]*\\([A-Za-z_$][A-Za-z0-9_$]+\\)[ \t]*([a-zA-Z0-9, ]*) *\{ *$" 1) ;; es6 fn1 () { }
    ;;         ("Function" "^[ \t]*\\([A-Za-z_$][A-Za-z0-9_$]+\\)[ \t]*=[ \t]*(?[a-zA-Z0-9, ]*)?[ \t]*=>" 1) ;; es6 fn1 = (e) =>
    ;;         ;; }}
    ;;         ("Task" "[. \t]task([ \t]*['\"]\\([^'\"]+\\)" 1)
    ;; ))
    ;; ;; js-mode imenu enhancement
    ;; ;; @see http://stackoverflow.com/questions/20863386/idomenu-not-working-in-javascript-mode
    ;; (defun mo-js-imenu-make-index ()
    ;;   (save-excursion
    ;;     (imenu--generic-function javascript-common-imenu-regex-list)))
    ;; (defun mo-js-mode-hook ()
    ;;   (when (and (not (is-buffer-file-temp)) (not (derived-mode-p 'js2-mode)))
    ;;     (my-common-js-setup)
    ;;     (setq imenu-create-index-function 'mo-js-imenu-make-index)))
    ;; (add-hook 'js-mode-hook 'mo-js-mode-hook)
    (setq-default js2-basic-offset 4)
    ;; (with-eval-after-load 'js2-mode
    ;;   (load (expand-file-name "private/init-javascript.el" user-emacs-directory)))
)

;; Do not write anything past this comment. This is where Emacs will
;; auto-generate custom variable definitions.
(custom-set-variables
 ;; custom-set-variables was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
(custom-set-faces
 ;; custom-set-faces was added by Custom.
 ;; If you edit it by hand, you could mess it up, so be careful.
 ;; Your init file should contain only one such instance.
 ;; If there is more than one, they won't work right.
 )
