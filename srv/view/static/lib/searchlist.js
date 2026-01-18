/*
 * Display of the list of pairs of questions and answers.
 */

const React = window.React ?? (await import('react'));
const ReactDOM = window.ReactDOM ?? (await import('react-dom'));
import SearchQuestion from "arxifter/biorxiv/searchquestion.js";
import SearchWaiting from "arxifter/biorxiv/searchwaiting.js";
import SearchAnswer from "arxifter/biorxiv/searchanswer.js";
class SearchList extends React.Component {
  constructor(props) {
    super(props);
    {
      const iniSearchList = props.searchList ?? [];
      this.state = {
        toSaveLastSearches: props.getSaveLastSearches(),
        searchList: iniSearchList,
        // the same value of rankForSearchID can be used
        // for making a search ID of two different searches
        // if the searches do not come in the same ms
        // (even within-ms IDs should end up being different);
        // thus doing it in a way that requires a page reload
        // to have a possibility for such a situation,
        // since expecting that the combination of user action
        // within the UI and page reload takes more time;
        rankForSearchID: iniSearchList.length
      };
    }
    this.getToSaveLastSearches = () => {
      return this.state.toSaveLastSearches;
    };
    this.setToSaveLastSearches = doSaving => {
      this.setState({
        toSaveLastSearches: doSaving
      });
    };
    this.getSearchList = () => {
      return this.state.searchList;
    };
    this.removeSearch = id => {
      let searchList = [];
      this.state.searchList.forEach(item => {
        if (item.id != id) {
          searchList.push(item);
        }
      });
      this.setState({
        searchList: searchList
      });
      // it is necessary to provide the list here,
      // b/c its form in this.state.searchList
      // has the updated value only after re-rendering
      this.saveLastSearches(null, searchList);
    };
    this.saveLastSearches = (toSave, searchList) => {
      if (toSave ?? this.getToSaveLastSearches()) {
        storageSaveSearches(props.getStoragePrefix(), searchList ?? this.state.searchList, getFabricUi()["recallSearches"]);
      } else {
        storageCleanSearches(props.getStoragePrefix());
      }
    };
    this.addSearch = (isAnswer, content) => {
      // a single answer should come to any question,
      // and any answer should have a previous question,
      // but better to take it more dynamically;
      let searchList = this.state.searchList;
      const rankForSearchID = this.state.rankForSearchID;
      this.setState({
        // this value is generally not the rank of the item;
        rankForSearchID: rankForSearchID + 1
      });
      if (!isAnswer) {
        // a new question was made;
        searchList.push({
          id: utilsGenSearchID(rankForSearchID),
          question: content,
          answers: []
        });
        this.setState({
          searchList: searchList
        });
        return;
      }
      // if here, it is an answer;
      if (searchList.length == 0) {
        // if here, there is no previous question though;
        // this situation should not happen,
        // but better to take care about it too;
        searchList.push({
          id: utilsGenSearchID(rankForSearchID),
          question: {
            subject: "---",
            query: ""
          },
          answers: [content]
        });
        this.setState({
          searchList: searchList
        });
        return;
      }
      // adding an answer to a question;
      // it should always be with a single answer,
      // but doing it more generally;
      let lastQA = searchList.pop();
      lastQA.answers.push(content);
      searchList.push(lastQA);
      this.setState({
        searchList: searchList
      });
    };
  }
  render() {
    return /*#__PURE__*/React.createElement("div", {
      id: "search-list"
    }, this.state.searchList.slice().reverse().map((x, i) => /*#__PURE__*/React.createElement("div", {
      key: x.id
    }, i > 0 && /*#__PURE__*/React.createElement("hr", {
      key: `s_${x.id}`,
      className: "search-separator"
    }), x.question !== null && /*#__PURE__*/React.createElement(SearchQuestion, {
      key: `q_${x.id}`,
      rank: i,
      content: x.question,
      removal: () => this.removeSearch(x.id),
      removalActive: x.answers.length > 0
    }), i == 0 && x.answers.length == 0 && /*#__PURE__*/React.createElement(SearchWaiting, {
      key: `w_${x.id}`
    }), x.answers.map((y, j) => /*#__PURE__*/React.createElement(SearchAnswer, {
      key: `a_${x.id}_${j}`,
      content: y
    })))));
  }
}
export { SearchList as default };
