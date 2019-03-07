const withCss = require("@zeit/next-css");

// fix: prevents error when .css files are required by node
if (typeof require !== "undefined") {
  require.extensions[".css"] = () => null;
}

module.exports = withCss();
module.exports.publicRuntimeConfig = {
  PUBLIC_IP: process.env.PUBLIC_IP,
  ELASTIC_IP: process.env.ELASTIC_IP,
  ELASTIC_INDEX: process.env.ELASTIC_INDEX,
  // ELASTIC_PORT: process.env.ELASTIC_PORT,
  // REACT_PORT: process.env.REACT_PORT,
  // DWV_PORT: process.env.DWV_PORT
}
