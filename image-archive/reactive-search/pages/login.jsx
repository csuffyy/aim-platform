import React, { Component } from "react";
import {
  ReactiveBase,
  TagCloud,
  SelectedFilters,
  ResultCard
} from "@appbaseio/reactivesearch";
var cookie = require('cookie');
import Navbar from "./Navbar.js";
import Leftbar from "./Leftbar.js";
import initReactivesearch from "@appbaseio/reactivesearch/lib/server";
import "./index.css";

import getConfig from 'next/config';
const {publicRuntimeConfig} = getConfig();
const {PUBLIC_IP} = publicRuntimeConfig;
const {ELASTIC_PORT} = publicRuntimeConfig;
const {ELASTIC_IP} = publicRuntimeConfig;
const {ELASTIC_INDEX} = publicRuntimeConfig;
const {AUTH_TOKEN} = publicRuntimeConfig;

console.log('PUBLIC_IP: ' + PUBLIC_IP);
console.log('ELASTIC_PORT: ' + ELASTIC_PORT);
console.log('ELASTIC_IP: ' + ELASTIC_IP);
console.log('ELASTIC_INDEX: ' + ELASTIC_INDEX);
console.log('AUTH_TOKEN: ' + AUTH_TOKEN);

var today = new Date();
var expiry = new Date(today.getTime() + 30 * 24 * 3600 * 1000); // plus 30 days
function setCookie(name, value)
{
  document.cookie=name + "=" + escape(value) + "; path=/; expires=" + expiry.toGMTString();
}

class Main extends Component {
  constructor(props) {
    super(props);
    this.state = {username: '', password: ''};

    this.handleChangePassword = this.handleChangePassword.bind(this);
    this.handleChangeUsername = this.handleChangeUsername.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
  }

  handleChangeUsername(event) {
    console.log(event);
    console.log(event.target);
    console.log(event.target.value);
    // this.state.username=event.target.value;
    this.setState({username: event.target.value});
  }

  handleChangePassword(event) {
    console.log(event);
    console.log(event.target);
    console.log(event.target.value);
    // this.state.password=event.target.value;
    this.setState({password: event.target.value});
  }

  handleSubmit(event) {
    console.log(event);
    console.log(this);
    console.log(this.state);
    setCookie('token', this.state.password);
    // event.preventDefault();
  }

  static async getInitialProps({res, req}) {
    // Parse the cookies on the request
    var cookies = cookie.parse(req.headers.cookie || '');
    
    // Get the visitor name set in the cookie
    var token = cookies.token;
    console.log('token: ' + token);
    console.log('AUTH_TOKEN: ' + AUTH_TOKEN);

    // // Set a Cookie
    // res.setHeader('Set-Cookie', cookie.serialize('token', '771100', {
    //   httpOnly: true,
    //   maxAge: 60 * 60 * 24 * 7 // 1 week
    // }));

    // Set a header
    // res.setHeader('X-Foo', 'bar');

    // Redirect to login if no token
    if (token === AUTH_TOKEN) {
      console.log('valid token')
      res.writeHead(302, {
        Location: '/'
      })
      res.end() // load nothing else
    }

    return {
      store: 'await'
    };
  }

  render() {
    return (
      <div className="main-container">
        <div className="login-box">
          {/*this.props.store: {this.props.store}*/}

          <div className="logo-container">
            <img
              className="app-logo"
              src="/static/sickkids.png"
              alt="ImageArchive"
            />
          </div>


          <h3 className="login-text">
            Diagnostic Image Archive
          </h3>

          <div className="login-div">
            <form onSubmit={this.handleSubmit}>
              <label>
                {/*<span>Username:</span>*/}
                <input className="login-field" type="text" value={this.state.username} onChange={this.handleChangeUsername} placeholder=" Username"/>
              </label>
              <p/>
              <label>
                {/*<span>Password:</span>*/}
                <input className="login-field" type="text" value={this.state.password} onChange={this.handleChangePassword} placeholder=" Password"/>
              </label>
              <p/>
              <input className="login-submit btn btn-secondary" type="submit" value="Login" />
            </form>
          </div>
          <div className="login-footer">
            <a className="login-footer-link" href="mailto:daniel.snider@sickkids.ca?subject=Diagnostic Image Archive Support" target="_blank">Support</a> Provided by <a className="login-footer-link" href="https://ccm.sickkids.ca/" target="_blank">The CCM</a>
          </div>
        </div>
      </div>
    );
  }
}
export default Main;
