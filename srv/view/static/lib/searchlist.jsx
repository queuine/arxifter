/*
 * Display of the list of pairs of questions and answers.
 */

const React = window.React ?? await import('react');
const ReactDOM = window.ReactDOM ?? await import('react-dom');

import SearchQuestion from "arxifter/biorxiv/searchquestion.js";
import SearchWaiting from "arxifter/biorxiv/searchwaiting.js";
import SearchAnswer from "arxifter/biorxiv/searchanswer.js";

class SearchList extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            searchList: [],
            endRank: -1
        };
        this.addSearch = (isAnswer, content) => {
            // a single answer should come to any question,
            // and any answer should have a previous question,
            // but better to take it more dynamically;
            let searchList = this.state.searchList;
            if (!isAnswer) {
                // a new question was made;
                searchList.push({question: content, answers: []});
                this.setState({
                    searchList: searchList,
                    endRank: this.state.endRank + 1
                });
                return;
            }
            // if here, it is an answer;
            if (searchList.length == 0) {
                // if here, there is no previous question though;
                // this situation should not happen,
                // but better to take care about it too;
                searchList.push({question: null, answers: [content]});
                this.setState({
                    searchList: searchList,
                    endRank: this.state.endRank + 1
                });
                return;
            }
            // adding an answer to a question;
            // it should always be with a single answer,
            // but doing it more generally;
            let lastQA = searchList.pop();
            lastQA.answers.push(content);
            searchList.push(lastQA);
            this.setState({ searchList: searchList });
        }
    }

    render() {
        return (
            <div id="search-list">
                {
                    this.state.searchList.slice().reverse().map((x, i) => (
                    <div
                        key={this.state.endRank - i}
                    >
                        {
                            (i > 0) &&
                            <hr
                                key={`s_${this.state.endRank - i}`}
                                className="search-separator"
                            />
                        }
                        {
                            (x.question !== null) &&
                            <SearchQuestion
                                key={`q_${this.state.endRank - i}`}
                                content={x.question}
                            />
                        }
                        {
                            ((i == 0) && (x.answers.length == 0)) &&
                            <SearchWaiting
                                key={`w_${this.state.endRank - i}`}
                            />
                        }
                        {
                            x.answers.map((y, j) => (
                                <SearchAnswer
                                    key={`a_${this.state.endRank - i}_${j}`}
                                    content={y}
                                />
                            ))
                        }
                    </div>
                    ))
                }
            </div>
        );
    }
}

export { SearchList as default };
