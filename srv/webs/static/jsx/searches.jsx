
class BiorxivSearches extends React.Component {
    constructor() {
        super();
        this.state = {
            searchList: []
        };
        this.addSearch = (isAnswer, content) => {
            let searchList = this.state.searchList;
            searchList.push({isAnswer: isAnswer, content: content});
            this.setState(({ searchList: searchList }));
        }
    }

    render() {
        return (
            <div id="biorxiv-searches">
                {
                    this.state.searchList.map((x, i) => (
                        x.isAnswer
                        ?
                        <BiorxivAnswer
                            key={i}
                            rank={i}
                            content={x.content}
                        />
                        :
                        <BiorxivQuestion
                            key={i}
                            rank={i}
                            content={x.content}
                        />
                    ))
                }
            </div>
        );
    }
}
