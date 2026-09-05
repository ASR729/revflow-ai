const Document = require('next/document').default;
const { Html, Head, Main, NextScript } = require('next/document');
const React = require('react');

class MyDocument extends Document {
  static async getInitialProps(ctx) {
    const initialProps = await Document.getInitialProps(ctx);
    return { ...initialProps };
  }

  render() {
    return React.createElement(Html, { lang: 'en' },
      React.createElement(Head, null),
      React.createElement('body', null,
        React.createElement(Main, null),
        React.createElement(NextScript, null)
      )
    );
  }
}

module.exports = MyDocument;