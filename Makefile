PREFIX  ?= /usr/local
PYTHON  ?= python3
APP     = viper
SRC_DIR = viper

.PHONY: run install uninstall check-deps help

help:
	@echo ""
	@echo "  VIPER — A minimal Python compiler for Linux"
	@echo "  ─────────────────────────────────────────────"
	@echo ""
	@echo "  make run          Run Viper"
	@echo "  make install      Install to $(PREFIX) (needs sudo)"
	@echo "  make uninstall    Remove from $(PREFIX) (needs sudo)"
	@echo "  make check-deps   Check python3-tk is available"
	@echo ""

check-deps:
	@$(PYTHON) -c "import tkinter" 2>/dev/null && \
		echo "✓ tkinter is installed" || \
		(echo "✗ tkinter not found. Install it:" && \
		 echo "  Ubuntu/Debian:  sudo apt install python3-tk" && \
		 echo "  Fedora:         sudo dnf install python3-tkinter" && \
		 echo "  Arch:           sudo pacman -S tk" && \
		 exit 1)

run: check-deps
	@PYTHONPATH=. $(PYTHON) -m $(APP)

install: check-deps
	# Install package files
	install -d $(DESTDIR)$(PREFIX)/lib/$(APP)/viper
	install -m 644 $(SRC_DIR)/*.py $(DESTDIR)$(PREFIX)/lib/$(APP)/viper/
	
	# Install launcher script
	install -d $(DESTDIR)$(PREFIX)/bin
	@echo '#!/bin/sh' > $(DESTDIR)$(PREFIX)/bin/$(APP)
	@echo 'export PYTHONPATH=$(PREFIX)/lib/$(APP):$$PYTHONPATH' >> $(DESTDIR)$(PREFIX)/bin/$(APP)
	@echo 'exec $(PYTHON) -m viper "$$@"' >> $(DESTDIR)$(PREFIX)/bin/$(APP)
	chmod 755 $(DESTDIR)$(PREFIX)/bin/$(APP)
	
	# Install Desktop entry and Icon for App Gallery
	install -d $(DESTDIR)/usr/share/applications
	install -m 644 $(APP).desktop $(DESTDIR)/usr/share/applications/
	install -d $(DESTDIR)/usr/share/pixmaps
	install -m 644 $(APP).png $(DESTDIR)/usr/share/pixmaps/
	
	# Update desktop database if it exists
	-update-desktop-database /usr/share/applications 2>/dev/null || true
	
	@echo ""
	@echo "✓ Viper installed successfully!"
	@echo "✓ You can now launch it from your Applications Gallery."
	@echo "✓ Or run it from terminal with: $(APP)"

uninstall:
	rm -rf $(DESTDIR)$(PREFIX)/lib/$(APP)
	rm -f $(DESTDIR)$(PREFIX)/bin/$(APP)
	rm -f $(DESTDIR)/usr/share/applications/$(APP).desktop
	rm -f $(DESTDIR)/usr/share/pixmaps/$(APP).png
	-update-desktop-database /usr/share/applications 2>/dev/null || true
	@echo "✓ Viper uninstalled"
