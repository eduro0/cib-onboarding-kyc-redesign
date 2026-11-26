# Spec

What we want, one plain sentence per rule. `product/` is what we deliver; `contributing/` is how we work. One file
per area; the file name is the area. Each file ends with "Where this is enforced": the files that enforce each rule
and the checks that prove it. `not yet` is fine until it's built, `reviewer` means the review checks it by hand, and
`owner` means only the owner can.

Mark each product statement `(decided)`, `(default, owner to confirm)` or `(guess)`, so the spec also shows what is
still open. Describe how things are now, never how they got there.

Product statements name project files as their enforcers, never the kit's own files (`checks/check.py`): the
back-pointer rule would otherwise want project statement IDs inside a shared kit file.
