#
# Transpile React .jsx files to JavaScript .js files.
#

BABELCMD=babeljs
JSXDIR=static/lib

SRC = $(wildcard $(JSXDIR)/*.jsx)
DST = $(SRC:$(JSXDIR)/%.jsx=$(JSXDIR)/%.js)

dst: $(DST)
$(JSXDIR)/%.js: $(JSXDIR)/%.jsx
	$(BABELCMD) --presets @babel/preset-react $< -o $@

clean:
	rm -f $(JSXDIR)/*.js

