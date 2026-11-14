const response = $input.first().json;
let text = response.answer || "No response received.";

if (response.citations && response.citations.length > 0) {
  text += "\n\n---\n#### Manual References\n";
  const seen = new Set();
  response.citations.forEach((c) => {
    const key = (c.manual_name || '') + '-' + (c.page || '');
    if (!seen.has(key)) {
      seen.add(key);
      const pageLabel = c.page ? ("Page " + c.page) : "Document";
      const pageLink = c.url ? ("[" + pageLabel + "](" + c.url + ")") : ("**" + pageLabel + "**");
      text += "- **" + c.manual_name + "** — " + pageLink + " (*" + (c.section || "General") + "*)\n";
    }
  });
}

return [{ json: { response: text, text: text, output: text } }];
