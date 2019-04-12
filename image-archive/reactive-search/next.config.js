const withCss = require("@zeit/next-css");

// fix: prevents error when .css files are required by node
if (typeof require !== "undefined") {
  require.extensions[".css"] = () => null;
}

module.exports = withCss();
module.exports.publicRuntimeConfig = {
  PUBLIC_URL: process.env.PUBLIC_IP,
  ELASTIC_URL: process.env.ELASTIC_URL,
  ELASTIC_INDEX: process.env.ELASTIC_INDEX,
  AUTH_TOKEN: process.env.AUTH_TOKEN,
  FILESERVER_TOKEN: process.env.FILESERVER_TOKEN,
  STATIC_WEBSERVER_URL: process.env.STATIC_WEBSERVER_URL,
  DWV_URL: process.env.DWV_URL
}
